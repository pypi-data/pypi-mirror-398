import datetime
from pathlib import Path
import logging

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import sa_gwdata
import pypdf

from .sageodata_database import connect as connect_to_sageodata
from .hydstra import *
from .utils import *


logger = logging.getLogger(__name__)


def add_construction_activity_column(df):
    """Add a new column "activity" to the result of a query
    over the CONSTRUCTION_SUMMARY table in SA Geodata.

    Args:
        df (pandas.DataFrame): this should contain the columns
            "screened", "pcemented", "developed", "abandoned",
            "backfilled", "dry", "enlarged", "flowing", "replacement",
            "rehabilitated", and "core_flag", and they should contain
            either "Y" or "N".

    Returns:
        pandas.DataFrame: The returned table has the same columns
        as **df** with an additional column "activity" that contains
        the names of the columns mentioned above which contain "Y"
        e.g. if "screened" = Y and "flowing" = Y then the activity
        column will contain "screened + flowing".

    """
    bool_flags = [
        "screened",
        "pcemented",
        "developed",
        "abandoned",
        "backfilled",
        "dry",
        "enlarged",
        "flowing",
        "replacement",
        "rehabilitated",
        "core_flag",
    ]
    df["activity"] = df.apply(
        lambda row: " + ".join([col for col in bool_flags if row.get(col, "N") == "Y"]),
        axis=1,
    )
    return df


def apply_latest_status(
    df,
    as_col="latest_status",
    dh_no_col="dh_no",
    status_code_col="status_code",
    status_date_col="status_date",
):
    """For a spreadsheet that has multiple rows of status information,
    coalesce those into a "latest status" field.

    Args:
        df (pandas.DataFrame): Table of data with status information e.g.
            obtained from ``db.drillhole_status()``
        as_col (str): name of new column to be created
        dh_no_col (str): column with drillhole numbers
        status_code_col (str): column with status codes
        status_date_col (str): column with status code dates

    Returns:
        pandas.DataFrame: The returned table has a new column
        **as_col**.

    For example:

    .. code-block:: python

        >>> db = gd.sageodata()
        >>> wells = db.wells_in_groups(["CENT_ADEL"])
        >>> df = db.drillhole_status(wells)
        >>> df[['obs_no', 'status_code', 'status_desc', 'status_date']].head()
            obs_no status_code    status_desc status_date
        0    PTA040         OPR    Operational  1998-09-25
        1    PTA040         RHB  Rehabilitated  1992-02-20
        2    PTA060         BKF     Backfilled  2014-04-01
        3    PTA060         BLK        Blocked  2013-12-10
        4    PTA060         OPR    Operational  1998-09-25
        >>> df2 = gd.apply_latest_status(df)
        >>>  df2[['obs_no', 'latest_status', 'status_code', 'status_desc', 'status_date']].head()
            obs_no latest_status status_code    status_desc status_date
        0    PTA040           OPR         OPR    Operational  1998-09-25
        1    PTA040           OPR         RHB  Rehabilitated  1992-02-20
        2    PTA060           BKF         BKF     Backfilled  2014-04-01
        3    PTA060           BKF         BLK        Blocked  2013-12-10
        4    PTA060           BKF         OPR    Operational  1998-09-25

    """
    df2 = df.copy()

    def get_latest_code_for_drillhole(df):
        dates = [d for d in df[status_date_col].unique() if pd.notnull(d)]
        if len(dates):
            max_date = max(dates)
            max_codes = df[df[status_date_col] == max_date][status_code_col]
            final_code = "+".join(sorted(max_codes.unique()))
        else:
            final_code = "+".join(sorted(df[status_code_col].unique()))
        return final_code

    df2.insert(
        list(df2.columns).index(status_code_col) - 1,
        as_col,
        df2.dh_no.map(df2.groupby(dh_no_col).apply(get_latest_code_for_drillhole)),
    )

    return df2


def fetch_wl_data(
    wells,
    include_replacements=False,
    ts_agg_ndays=5,
    ts_agg_methods=None,
    conn=None,
    aq=None,
    **kwargs,
):
    """Fetch and merge water level data from SA Geodata and Aquarius.

    DEPRECATED. get_combined_water_level_dataset should be used instead.

    Args:
        wells: either a list of :class:`sa_gwdata.Well` objects
            or a :class:`pandas.DataFrame` with a column
            "unit_long"
        include_replacements (bool): splice data from replacement wells for
            SA Geodata. ***NOTE***: this does NOT include AQTS data for
            replaced wells.
        conn (sageodata_db.Connection): server
        aq (dew_gwdata.DEWAquarius): server
        ts_agg_ndays (int or str): aggregate continuous TS data from AQTS to
            a given number of days or other interval. If you use an integer
            here it shold be the number of days. To provide a value in
            a different unit, provide a string composed of an integer
            value followed by one of these letters:
            - w = weeks
            - d = days
            - H = hours
            - M = minutes
            e.g. "2w" = 2 weeks, "7d" = 7 days, "12H" = 12 hours,
            "30M" = 30 minutes.
        ts_agg_methods (dict): how to aggregate AQ TS data.
            None means to use :func:`dew_gwdata.reduce_to_interval`'s
            default argument which assumes the dataset parameter being
            sought is "Depth to Water".

    Other keyword arguments are passed to
    :func:`dew_gwdata.DEWAquarius.fetch_timeseries_data`

    Aquarius data is retrieved from the AQTS production environment.

    Returns:
        pandas.DataFrame: xx

    """
    if conn is None:
        conn = connect_to_sageodata()
    if aq is None:
        from .aquarius_ts import DEWAquarius

        aq = DEWAquarius()

    logger.info(f"Requesting {len(wells)} wells: {wells}")

    try:
        assert isinstance(wells[0], sa_gwdata.Well)
        # It is a list of Well objects.
        potential_aq_sites = [w.unit_hyphen for w in wells]
    except (AssertionError, KeyError) as e:
        # It is a table e.g. from conn.drillhole_details()
        potential_aq_sites = wells.unit_hyphen.values

    # Filter to only those locations which exist in AQTS:
    aqdf = aq.fetch_locations_timeseries_metadata(potential_aq_sites)
    aq_sites = [u for u in aqdf.loc_id.unique()]
    logger.debug(
        f"Found {len(aq_sites)} of {len(wells)} wells as locations in AQTS: {aq_sites}"
    )

    logger.debug(
        f"Fetching SA Geodata water levels for all {len(potential_aq_sites)} wells"
    )
    wells = conn.find_wells(",".join([str(x) for x in potential_aq_sites]))

    logger.debug(f"Located {len(wells)} wells.\n{str(wells.dh_no)}")
    sag_wls = conn.water_levels(wells.dh_no, include_replacements=include_replacements)
    sag_wls["database"] = "SA Geodata"

    aq_dfs = {}
    if len(aq_sites) > 0:
        aq_md = aq.fetch_locations_timeseries_metadata(aq_sites)
        for aq_locid in aq_sites:
            aq_md2 = aq_md[
                (aq_md.loc_id == aq_locid)
                & (aq_md.param == "Depth to Water")
                & (aq_md.label.str.startswith("Best Available"))
                & (aq_md.label != "Best Available--Hydstra 110")
            ]
            logger.debug(
                f"Timeseries found for {aq_locid}:\n{aq_md2[['param', 'label']]}"
            )
            if len(aq_md2) == 0:
                ts_uid = None
                logger.debug(f"none found - skipping.")
            elif len(aq_md2) == 1:
                ts_uid = aq_md2.ts_uid.iloc[0]
                logger.debug(f"one found - using {ts_uid}")
            else:
                ts_uid = aq_md2.ts_uid.iloc[0]
                logger.warning(f"multiple timeseries: using {ts_uid}")
            if not ts_uid is None:
                logger.debug(f"Fetching AQTS data for {aq_locid} ts_uid={ts_uid}")
                dfs = aq.fetch_timeseries_data(ts_uid=ts_uid, **kwargs)
                df = join_logger_data_intervals(dfs, param_if_empty="dtw")
                #     locid=aq_locid, param="Depth to Water", label=label, label_startswith=False
                # )
                logger.debug(f"fetched {len(df)} data points")
                logger.debug(
                    f"before reduction to {ts_agg_ndays} days ts_agg_methods={ts_agg_methods}: {len(df)} data points, {df.columns}"
                )
                if len(df):
                    logger.debug(f"df columns = {df.columns}")
                    df = reduce_to_interval(
                        df, ts_agg_ndays, dt_col="timestamp", aggs=ts_agg_methods
                    )
                else:
                    logger.debug("skipped reduction - df has no records")
                logger.debug(f"after reduction: {len(df)} data points, {df.columns}")
                df = df.rename(
                    columns={"Depth to Water": "dtw", "timestamp": "obs_date"}
                )
                df["unit_hyphen"] = aq_locid
                if len(df):
                    df["obs_date"] = df.obs_date.dt.tz_localize(None)
                aq_dfs[aq_locid] = df

    if len(aq_dfs):
        aqdf = pd.concat(aq_dfs)

        elevs = conn.elevation_surveys(wells)
        logger.debug(f'Fetched AQTS DTW for\n{aqdf.groupby("unit_hyphen").dtw.count()}')

        series = transform_dtw_to_rswl(aqdf, elevs, well_id_col="unit_hyphen")
        aqdf["rswl"] = series.values
        aqdf["database"] = "Aquarius"
        aqdf["anomalous_ind"] = "N"
        aqdf.loc[aqdf.grade <= 0, "anomalous_ind"] = "Y"
        logger.debug(
            f'Calculated RSWL for data from AQTS for\n{aqdf.groupby("unit_hyphen").rswl.count()}'
        )
        if len(aqdf):
            dh_details = conn.drillhole_details(
                conn.find_wells(",".join([str(u) for u in aqdf.unit_hyphen.unique()]))
            )
            aqdf = pd.merge(
                dh_details,
                aqdf[[x for x in aqdf.columns if not x == "well_id"]],
                how="outer",
                on="unit_hyphen",
            )
            ret_df = pd.concat([sag_wls, aqdf], sort=False).sort_values(
                by=["unit_long", "obs_date"]
            )
        else:
            ret_df = sag_wls
    else:
        ret_df = sag_wls.sort_values(by=["unit_long", "obs_date"])

    # make sure all columns are present.
    extra_cols = {
        "database": "",
        "quality_code": pd.NA,
        "grade": pd.NA,
    }
    for col, value in extra_cols.items():
        if not col in ret_df:
            ret_df[col] = value
    return ret_df


def reduce_to_interval(
    df,
    ndays=5,
    dt_col="obs_date",
    aggs=None,
):
    """Reduce to a less frequent daily interval e.g. daily, weekly, monthly.

    Args:
        df (pandas.DataFrame): dataset
        ndays (int or str): number of days (interval length) if provided
            as an integer. If provided as a string it must be an integer number
            followed immediately by one of the following:
            - w = weeks
            - d = days
            - H = hours
            - M = minutes
            e.g.  2w = 2 weeks, 7d = 7 days, 12H = 12 hours,
            30M = 30 minutes.
        dt_col (str): name of column in *df* containing the timestamps
        aggs (dict): optional dictionary. keys are column names and values
            are functions to aggregate (or string value shortcuts used in pandas
            groupby.aggregate e.g. "mean", "min", "first").

    Returns:
        pandas.DataFrame: The index is a set of datetime objects spaced at an
        interval of *ndays*; the values are those from *data_col*, aggregated by
        the method *agg_method*.

    """
    grouper_mapping = {
        "w": "W",
        "d": "d",
        "H": "h",
        "M": "min",
    }
    timedelta_mapping = {
        "w": "W",
        "d": "day",
        "H": "h",
        "M": "m",
    }
    if aggs is None:
        aggs = {
            "grade": "min",
            "approval": "first",
            "qualifier": "first",
        }
        for col in ["Depth to Water", "dtw", "SWL", "swl", "RSWL", "rswl", "tds", "ec"]:
            if col in df.columns:
                aggs[col] = "mean"

    if isinstance(ndays, int):
        period = ndays
        grouper_freq = grouper_mapping["d"]
        timedelta_freq = timedelta_mapping["d"]
    else:
        period = int(ndays[:-1])
        grouper_freq = grouper_mapping[ndays[-1]]
        timedelta_freq = timedelta_mapping[ndays[-1]]

    print(f"Reducing data by {period}{timedelta_freq} dt_col={dt_col} aggs={aggs}")
    offset = pd.Timedelta(period, timedelta_freq) / 2
    grouper = pd.Grouper(key=dt_col, freq=f"{period:.0f}{grouper_freq}", label="left")
    print(f"offset={offset} grouper={grouper}")
    df2 = df.groupby(grouper)[list(aggs.keys())].agg(aggs)
    df2 = df2.shift(1, freq=(offset)).reset_index()
    return df2


def transform_dtw_to_rswl(
    edf,
    elevs,
    well_id_col="unit_long",
    dt_col="obs_date",
    dtw_col="dtw",
    rswl_col="rswl",
):
    return transform_dtw_to_swl_and_rswl(
        edf,
        elevs,
        join_col=well_id_col,
        wls_dt_col=dt_col,
        wls_dtw_col=dtw_col,
    )["rswl"]


# def transform_dtw_to_rswl(
#     edf,
#     elevs,
#     well_id_col="unit_long",
#     dt_col="obs_date",
#     dtw_col="dtw",
#     rswl_col="rswl",
# ):
#     """Convert depth to water (m) to reduced standing water level (m AHD).

#     Args:
#         edf (:class:`pandas.DataFrame`): water level observations
#         elevs (:class:`pandas.DataFrame`): elevation surveys from SA Geodata
#             (see :meth:`dew_gwdata.SAGeodataConnection.elevation_surveys`)
#         well_id_col (str): if *edf* and *elevs* have data from more than one
#             well in them, you will need to provide the field name which can
#             be used to correlate data between the two dataframes. By default,
#             when using Hydstra and SA Geodata, this value should be "unit_long"
#         dt_col (str): column with WL measurement date in *edf*
#         dtw_col (str): column with DTW measurement in *edf*
#         rswl_col (str): column to be created with RSWL measurement

#     Returns: :class:`pandas.Series`

#     Example:

#         >>> import dew_gwdata as gd
#         >>> db = gd.sageodata()
#         >>> wells = db.find_wells('PLL019')
#         >>> df = db.water_levels(wells)
#         >>> elevs = db.elevation_surveys(wells)
#         >>> df["rswl_custom"] = gd.transform_dtw_to_rswl(df, elevs)

#     """
#     if len(edf) == 0:
#         return pd.Series(name=rswl_col)

#     def per_well_apply(well_df):
#         well_elevs = elevs[elevs[well_id_col] == well_df[well_id_col].iloc[0]]
#         x = transform_dtw_to_rswl(
#             well_df,
#             well_elevs,
#             well_id_col=None,
#             dt_col=dt_col,
#             dtw_col=dtw_col,
#             rswl_col=rswl_col,
#         )
#         if not isinstance(x, pd.DataFrame):
#             x = x.to_frame()
#         return x

#     if well_id_col in edf and well_id_col in elevs:
#         results = edf.groupby(well_id_col, as_index=False).apply(per_well_apply)
#         return results.droplevel(0)[rswl_col]

#     if "well_id" in edf:
#         logger.debug(f'Calculating DTW -> RSWL transform for {edf["well_id"].unique()}')
#     edf2 = edf.copy()
#     edf2[rswl_col] = np.nan
#     elevs["ref_elev"] = pd.to_numeric(elevs["ref_elev"])
#     elev_records = elevs.to_dict(orient="records")
#     if len(elevs) == 0:
#         logger.debug("No elevation records present")
#         return edf2
#     if len(elevs) == 1:
#         logger.debug("One elevation record present.")
#         elev = elev_records[0]
#         if isinstance(elev["applied_date"], pd.Timestamp):
#             logger.debug(f'Applied date of {elev["applied_date"]} exists')
#             if not np.isnan(elev["ref_elev"]):
#                 edf2.loc[edf2[dt_col] >= elev["applied_date"], rswl_col] = (
#                     elev["ref_elev"] - edf2[dtw_col]
#                 )
#             elif not np.isnan(elev["ground_elev"]):
#                 edf2.loc[edf2[dt_col] >= elev["applied_date"], rswl_col] = (
#                     elev["ground_elev"] - edf2[dtw_col]
#                 )
#         else:
#             logger.debug("No applied date exists")
#             if not np.isnan(elev["ref_elev"]):
#                 edf2.loc[:, rswl_col] = elev["ref_elev"] - edf2[dtw_col]
#             elif not np.isnan(elev["ground_elev"]):
#                 edf2.loc[:, rswl_col] = elev["ground_elev"] - edf2[dtw_col]
#     else:
#         logger.debug(f"{len(elevs)} elevation records found")
#         if np.any([isinstance(x["applied_date"], pd.Timestamp) for x in elev_records]):
#             logger.debug("At least one applied date exists")
#             # There is at least one applied date.
#             applied_recs = sorted(
#                 [e for e in elev_records if e["applied_date"]],
#                 key=lambda x: x["applied_date"],
#             )

#             if np.all([~pd.isnull(x["ref_elev"]) for x in applied_recs]):
#                 logger.debug("All records have finite ref_elev")
#                 for elev in elev_records:
#                     idx = edf2[dt_col] >= elev["applied_date"]
#                     edf2.loc[idx, rswl_col] = (elev["ref_elev"] - edf2[dtw_col])[idx]
#             elif np.all([~pd.isnull(x["ground_elev"]) for x in applied_recs]):
#                 logger.debug("All records have finite ground_elev")
#                 for elev in elev_records:
#                     idx = edf2[dt_col] >= elev["applied_date"]
#                     edf2.loc[idx, rswl_col] = (elev["ground_elev"] - edf2[dtw_col])[idx]
#         else:
#             elev = sorted(elev_records, key=lambda x: x["elev_date"])[-1]
#             logger.debug(
#                 f'No records have an applied_date. Therefore using most recent data of {elev["elev_date"]}'
#             )
#             if not np.isnan(elev["ref_elev"]):
#                 edf2.loc[:, rswl_col] = elev["ref_elev"] - edf2[dtw_col]
#             else:
#                 edf2.loc[:, rswl_col] = elev["ground_elev"] - edf2[dtw_col]

#     return edf2[rswl_col]


def calculate_swl_and_rswl_from_dtw(dtw, ref_elev, ground_elev):
    """Convert depth to water (DTW) to standing water level (SWL)
    and reduced standing water level (RSWL).

    Uses the rules implemented in SA Geodata i.e. if both reference
    and ground elevations are not known, DTW is assumed to be the
    same as SWL.

    Args:
        dtw (float): depth to water measured increasing downwards
            from reference point.
        ref_elev (float): elevation of reference point measured
            increasing upwards from a reference datum
        ground_elev (float): elevation of ground surface measured
            increasing upwards from a reference datum.

    Returns:
        tuple: swl, rswl (two floats). SWL (Standing Water Level)
        is the depth to water measured from the ground surface,
        increasing downwards. RSWL (Reduced Standing Water Level)
        is the water elevation measured from the reference datum,
        increasing upwards.

    """
    if not pd.isnull(ref_elev):
        rswl = ref_elev - dtw
        if not pd.isnull(ground_elev):
            swl = dtw - (ref_elev - ground_elev)
        else:
            swl = dtw
    else:
        swl = dtw
        if not pd.isnull(ground_elev):
            rswl = ground_elev - dtw
        else:
            rswl = pd.NA
    return swl, rswl


def transform_dtw_to_swl_and_rswl_for_single_well(
    wls,
    elevs,
    wls_dtw_col="dtw",
    wls_date_col="obs_date",
    elevs_survey_date_col="elev_date",
    elevs_applied_date_col="applied_date",
    elevs_ref_col="ref_elev",
    elevs_ground_col="ground_elev",
    elevs_idx_col="elev_no",
):
    """Convert water levels measured in depth to water (DTW)
    to standing water level (SWL) and reduced standing water
    level (RSWL) for a single well.

    Args:
        wls (pd.DataFrame): must contain DTW measurements
            and observation dates.
        elevs (pd.DataFrame): must contain applied-from date,
            survey date, reference elevation data, ground
            elevation data, and record number. Some of these
            fields can be blank.
        wls_dtw_col (str): 'dtw' by default
        wls_date_col (str): 'obs_date' by default
        elevs_survey_date_col (str): 'elev_date' by default
        elevs_applied_date_col (str): 'applied_date' by default
        elevs_ref_col (str): 'ref_elev' by default
        elevs_ground_col (str): 'ground_elev' by default
        elevs_idx_col (str): 'elev_no' by default

    Returns:
        pandas.DataFrame: Contains two columns 'swl' and
        'rswl'. The index is identical to wls argument.

    Definitions:

    - DTW = increasing downwards from reference point
    - SWL = increasing downwards from ground level
    - RSWL = increasing upwards from reference datum
    - reference elevation = increasing upwards from reference
      datum
    - ground elevation = increasing upwards from reference
      datum

    """
    new_records = []
    for idx, wl in wls.iterrows():
        ref_elev = pd.NA
        ground_elev = pd.NA
        if pd.isnull(wl[wls_dtw_col]):
            swl = pd.NA
            rswl = pd.NA
        elif not pd.isnull(wl[wls_dtw_col]):
            if len(elevs) == 0:
                break

            applied_elevs = elevs[~pd.isnull(elevs[elevs_applied_date_col])]
            applied_elevs = applied_elevs.sort_values(
                [elevs_applied_date_col, elevs_survey_date_col, elevs_idx_col]
            )
            if len(applied_elevs):

                if pd.isnull(wl[wls_date_col]):
                    obs_date = pd.Timestamp("1800-01-01")
                else:
                    obs_date = wl[wls_date_col]

                relevant_applied_elevs = applied_elevs[
                    applied_elevs[elevs_applied_date_col] <= obs_date
                ]

                if len(relevant_applied_elevs) > 0:
                    ref_elev = relevant_applied_elevs.iloc[-1][elevs_ref_col]
                    ground_elev = relevant_applied_elevs.iloc[-1][elevs_ground_col]

                    swl, rswl = calculate_swl_and_rswl_from_dtw(
                        wl[wls_dtw_col], ref_elev, ground_elev
                    )
                else:
                    swl = pd.NA
                    rswl = pd.NA
            else:
                elev_sorted_1 = elevs.sort_values(
                    elevs_survey_date_col, ascending=False
                )
                if len(elev_sorted_1.dropna(subset=[elevs_survey_date_col])) > 0:
                    elev_sorted_2 = elev_sorted_1[
                        elev_sorted_1[elevs_survey_date_col]
                        == elev_sorted_1[elevs_survey_date_col].iloc[0]
                    ]
                else:
                    elev_sorted_2 = elev_sorted_1
                elev_sorted_2 = elev_sorted_2.sort_values(
                    [elevs_ref_col, elevs_idx_col]
                )
                ref_elev = elev_sorted_2.iloc[0][elevs_ref_col]
                ground_elev = elev_sorted_2.iloc[0][elevs_ground_col]

                swl, rswl = calculate_swl_and_rswl_from_dtw(
                    wl[wls_dtw_col], ref_elev, ground_elev
                )
        new_records.append(
            {
                "swl": swl,
                "rswl": rswl,
            }
        )
    new_wl_data = pd.DataFrame(new_records, index=wls.index)
    return new_wl_data


def transform_dtw_to_swl_and_rswl(
    wls,
    elevs,
    join_col="auto",
    wls_dtw_col="dtw",
    wls_date_col="obs_date",
    elevs_survey_date_col="elev_date",
    elevs_applied_date_col="applied_date",
    elevs_ref_col="ref_elev",
    elevs_ground_col="ground_elev",
    elevs_idx_col="elev_no",
):
    """Convert water levels measured in depth to water (DTW)
    to standing water level (SWL) and reduced standing water
    level (RSWL) for one or more wells.

    Args:
        wls (pd.DataFrame): must contain DTW measurements
            and observation dates.
        elevs (pd.DataFrame): must contain applied-from date,
            survey date, reference elevation data, ground
            elevation data, and record number. Some of these
            fields can be blank.
        wls_dtw_col (str): 'dtw' by default
        wls_date_col (str): 'obs_date' by default
        elevs_survey_date_col (str): 'elev_date' by default
        elevs_applied_date_col (str): 'applied_date' by default
        elevs_ref_col (str): 'ref_elev' by default
        elevs_ground_col (str): 'ground_elev' by default
        elevs_idx_col (str): 'elev_no' by default

    Returns:
        pandas.DataFrame: Contains a copy of the
        join_col, wls_dtw_col, and wls_date_col data plus
        two columns 'swl' and 'rswl'. The index is reset
        to ensure uniqueness.

    Definitions:

    - DTW = increasing downwards from reference point
    - SWL = increasing downwards from ground level
    - RSWL = increasing upwards from reference datum
    - reference elevation = increasing upwards from reference
      datum
    - ground elevation = increasing upwards from reference
      datum

    """
    if join_col == "auto":
        join_cols = [
            c
            for c in ["unit_hyphen", "unit_long", "dh_no", "obs_no"]
            if c in wls.columns and c in elevs.columns
        ]
        if len(join_cols) > 0:
            join_col = join_cols[0]
    dhs = wls[join_col].unique()
    records = []
    for dh_id in dhs:
        dh_wls = wls[wls[join_col] == dh_id]
        dh_elevs = elevs[elevs[join_col] == dh_id]
        corr_wls = transform_dtw_to_swl_and_rswl_for_single_well(
            dh_wls,
            dh_elevs,
            wls_dtw_col=wls_dtw_col,
            wls_date_col=wls_date_col,
            elevs_survey_date_col=elevs_survey_date_col,
            elevs_applied_date_col=elevs_applied_date_col,
            elevs_ref_col=elevs_ref_col,
            elevs_ground_col=elevs_ground_col,
            elevs_idx_col=elevs_idx_col,
        )
        records.append(
            pd.merge(
                dh_wls[[join_col, wls_date_col, wls_dtw_col]],
                corr_wls,
                left_index=True,
                right_index=True,
            )
        )
    if len(records) == 0:
        return pd.DataFrame(
            columns=[join_col, wls_dtw_col, wls_date_col, "swl", "rswl"]
        )
    else:
        return pd.concat(records)


def make_drillhole_events_table(
    wls,
    sals,
    const,
    elevs,
    wde_maint,
    wde_alerts,
    wde_logger_installs,
    wde_logger_reads,
):
    """Construct a table of events for a well.

    Args:
        wls (pandas.DataFrame): from predefined query "water_levels"
        sals (pandas.DataFrame): from predefined query "water_levels"
        const (pandas.DataFrame): from predefined query "water_levels"
        elevs (pandas.DataFrame): from predefined query "water_levels"
        wde_maint (pandas.DataFrame): from predefined WDE query "maintenance_issues" with
            additional columns "well_id" and "unit_hyphen"
        wde_alerts (pandas.DataFrame): from predefined WDE query "alerts" with
            additional columns "well_id" and "unit_hyphen"
        wde_logger_installs (pandas.DataFrame): from predefined WDE query "logger_installations" with
            additional columns "well_id" and "unit_hyphen"
        wde_logger_reads (pandas.DataFrame): from predefined WDE query "logger_readings" with
            additional columns "well_id" and "unit_hyphen"

    Returns: pandas DataFrame with columns:

    - well_id
    - event_date
    - event_type
    - param_type
    - param_value
    - details
    - comments
    - created_by
    - creation_date
    - modified_by
    - modified_date

    """

    # Water levels
    wls = wls.rename(columns={"obs_date": "event_date"}).assign(
        event_type="Water level",
        details="",
        param_type="",
        param_value="",
        comments="",
    )
    if len(wls.rswl.dropna()) > 0:
        wls["param_type"] = "DTW | SWL | RSWL"
        wls["param_value"] = wls.apply(
            (lambda row: f"{row.dtw:.2f} | {row.swl:.2f} | {row.rswl:.2f}"),
            axis="columns",
        )
    else:
        wls["param_type"] = "DTW | SWL"
        wls["param_value"] = wls.apply(
            (lambda row: f"{row.dtw:.2f} | {row.swl:.2f}"), axis="columns"
        )

    # Salinity
    sals = sals.rename(columns={"collected_date": "event_date"}).assign(
        event_type="Salinity",
        param_type="EC | TDS",
        param_value="",
        details="",
    )
    sals["details"] = sals.apply(
        (lambda row: f"{row.extract_method} by {row.collected_by}"),
        axis="columns",
    )
    sals["param_value"] = sals.apply(
        (lambda row: f"{row.ec:.0f} | {row.tds:.0f}"), axis="columns"
    )

    # Construction events
    const = const.rename(
        columns={
            "completion_date": "event_date",
            "current_depth": "param_value",
            #             "construction_aquifer": "details",
        }
    ).assign(
        param_type="Current depth",
        details="",
    )
    const["event_type"] = const.event_type.map({"C": "Construction", "S": "Survey"})
    const["comments"] = const.apply(
        (
            lambda row: (
                f"{'Aquifer: ' + row.construction_aquifer + ' ' if row.construction_aquifer else ''}"
                f"{row.comments}"
            )
        ),
        axis="columns",
    )

    # Elevation surveys
    elevs = elevs.rename(columns={"elev_date": "event_date"}).assign(
        event_type="Elevation survey",
        param_type="Ground | Ref. pt",
        param_value="",
        details="",
    )
    elevs["param_value"] = elevs.apply(
        (lambda row: f"{row.ground_elev} | {row.ref_elev}"), axis="columns"
    )
    elevs["details"] = elevs.apply(
        (
            lambda row: (
                f"{row.ref_point_type} ({row.ref_height}) "
                f"using {row.survey_meth} applied"
                f"{' from ' + row.applied_date.strftime('%Y-%m-%d') if not pd.isnull(row.applied_date) else ''}"
            )
        ),
        axis="columns",
    )

    # WDE maintenance
    wde_reports = wde_maint.rename(
        columns={"reported_date": "event_date", "reported_by": "created_by"}
    ).assign(
        event_type="WDE maintenance issue report",
        param_type="",
        param_value="",
        details="",
        creation_date=None,
        modified_by="",
        modified_date=None,
    )
    if len(wde_reports):
        wde_reports["details"] = wde_reports.priority.apply(lambda v: f"Priority {v}")

    wde_res = (
        wde_maint[~wde_maint.completed_date.isnull()]
        .rename(columns={"completed_date": "event_date", "created_by": "actioned_by"})
        .assign(
            event_type="WDE maintenance issue resolution",
            param_type="",
            param_value="",
            details="",
            creation_date=None,
            modified_by="",
            modified_date=None,
        )
    )
    if len(wde_res):
        wde_res["details"] = wde_res.priority.apply(lambda v: f"Priority {v}")
        wde_res["comments"] = wde_res.apply(
            (
                lambda row: (
                    f"{row.comments} resolved: "
                    f"{row.action_comments} {row.action_other}"
                )
            ),
            axis="columns",
        )

    # WDE alerts
    wde_alerts = wde_alerts.rename(
        columns={"creation_date": "event_date", "description": "comments"}
    ).assign(
        event_type="WDE alert",
        param_type="",
        param_value="",
        details="",
        creation_date=None,
        modified_by="",
        modified_date=None,
    )
    if len(wde_alerts):
        wde_alerts.loc[wde_alerts.active == True, "details"] = "Active"
        wde_alerts.loc[wde_alerts.active == False, "details"] = "Inactive"

    # Logger installations
    lg_inst = wde_logger_installs.rename(
        columns={"install_date": "event_date", "serial_no": "param_value"}
    ).assign(
        event_type="WDE Logger installation",
        param_type="S/N",
        creation_date=None,
        details="",
        created_by="",
        modified_by="",
        modified_date=None,
    )
    if len(lg_inst):
        lg_inst.loc[lg_inst.telemetry == True, "temp_telem"] = "Telemetered"
        lg_inst.loc[lg_inst.telemetry != True, "temp_telem"] = ""
        lg_inst["details"] = lg_inst.apply(
            (lambda row: f"{row.type} {row.model} {row.temp_telem}"),
            axis="columns",
        )

    # Logger readings
    lg_reads = wde_logger_reads.rename(
        columns={"reading_date": "event_date", "read_by": "created_by"}
    ).assign(
        event_type="WDE Logger read",
        param_type="Batt. | Mem. %",
        param_value="",
        details="",
        creation_date=None,
        modified_by="",
        modified_date=None,
    )
    if len(lg_reads):
        lg_reads["param_value"] = lg_reads.apply(
            (lambda row: f"{row.battery_pct} | {row.memory_pct}"), axis="columns"
        )

    # Chain together
    dfs = []
    cols = [
        "dh_no",
        "unit_hyphen",
        "well_id",
        "event_date",
        "event_type",
        "param_type",
        "param_value",
        "details",
        "comments",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    for df in (wls, sals, const, elevs, wde_reports, wde_alerts, lg_inst, lg_reads):
        if "event_date" in df:
            if len(df):
                df["event_date"] = df.event_date.dt.date
        df["comments"] = df.comments.fillna("")
        dfs.append(df[cols])
    df = pd.concat(dfs).sort_values("event_date")
    df = df[~pd.isnull(df.event_date)]
    return df


class StratigraphyHierarchy:
    """Tables of stratigraphic units and tools for working with them.

    Args:
        db (SAGeodataConnection): default None i.e. created as needed

    Other keywords args are passed to SAGeodataConnection i.e. for
    getting into QA or Dev; production  by default

    Attributes:
        strat (pd.DataFrame): a table of all stratigraphic units
        tlstrat (pd.DataFrame): a table of the top-level stratigraphic
            units as used in SA Geodata codes i.e. eons for the Precambrian, then
            periods for the Phanerozoic (but using Tertiary instead of Palaeogene
            and Neogene).

    The columns in strat are:

        >>> st = StratigraphyHierarchy()
        >>> st.strat.info()
        <class 'pandas.core.frame.DataFrame'>
        RangeIndex: 2536 entries, 0 to 2535
        Data columns (total 4 columns):
         #   Column                Non-Null Count  Dtype
        ---  ------                --------------  -----
         0   strat_unit_no         2536 non-null   int64
         1   parent_strat_unit_no  2422 non-null   float64
         2   map_symbol            2536 non-null   object
         3   strat_name            2536 non-null   object
        dtypes: float64(1), int64(1), object(2)
        memory usage: 79.4+ KB
        >>> print(st.strat.head())
           strat_unit_no  parent_strat_unit_no map_symbol                strat_name
        0           2960                   NaN          A            Archaean rocks
        1           4608                2960.0        A-c         Cooyerdoo Granite
        2           6684                4608.0       A-c1  Cooyerdoo Granite unit 1
        3           3462                2960.0        A-o           Coolanie Gneiss
        4           6685                2960.0         A1           Archaean unit 1

    tlstrat is:

        >>> st.tlstrat.info()
        <class 'pandas.core.frame.DataFrame'>
        Int64Index: 51 entries, 28 to 0
        Data columns (total 8 columns):
         #   Column                Non-Null Count  Dtype
        ---  ------                --------------  -----
         0   strat_unit_no         51 non-null     int64
         1   parent_strat_unit_no  0 non-null      object
         2   map_symbol            51 non-null     object
         3   strat_name            51 non-null     object
         4   start                 51 non-null     float64
         5   end                   51 non-null     float64
         6   oldest_unit           51 non-null     object
         7   youngest_unit         51 non-null     object
        dtypes: float64(2), int64(1), object(5)
        memory usage: 3.6+ KB
        >>> print(st.tlstrat[['strat_unit_no', 'map_symbol', 'strat_name']])
                    strat_unit_no map_symbol                               strat_name
        28           3106          Q                         Quaternary rocks
        35           3210         TQ               Tertiary-Pleistocene rocks
        34           3187          T                           Tertiary rocks
        49           6902         KT              Cretaceous toTertiary rocks
        50           2992        KTa               Cretaceous-Paleocene rocks
        48           2990          K                         Cretaceous rocks
        47           2989         JT                  Jurassic-Tertiary rocks
        46           4574         JK                Jurassic-Cretaceous rocks
        45           2986          J                           Jurassic rocks
        31           4760         RK                           Mesozoic rocks
        30           3185         RJ                  Triassic-Jurassic rocks
        29           3184          R                           Triassic rocks
        6            2968         CK           Carboniferous-Cretaceous rocks
        8            5815         CR             Carboniferous-Triassic rocks
        5            2967          C                      Carboniferous rocks
        25           6877         PQ                 Permian-Quaternary rocks
        27           6772         PT                   Permian-Tertiary rocks
        24           5650         PJ                   Permian-Jurassic rocks
        26           3103         PR                   Permian-Triassic rocks
        7            2970         CP              Carboniferous-Permian rocks
        23           2997          P                            Permian rocks
        9            2971          D                           Devonian rocks
        33           6020         SD                  Silurian-Devonian rocks
        32           3186          S                           Silurian rocks
        21           2995         OD                Ordovician-Devonian rocks
        22           5893         OS                Ordovician-Silurian rocks
        20           4421          O                         Ordovician rocks
        12           5281         EK                Cambrian-Cretaceous rocks
        14           2985         EP                         Palaeozoic rocks
        11           5593         ED                  Cambrian-Devonian rocks
        15           6790         ES                  Cambrian-Silurian rocks
        13           2978         EO                Cambrian-Ordovician rocks
        10           4698          E                           Cambrian rocks
        18           5013         NK          Neoproterozoic-Cretaceous rocks
        19           6445         NO          Neoproterozoic-Ordovician rocks
        17           2999         NE            Neoproterozoic-Cambrian rocks
        16           3037          N                     Neoproterozoic rocks
        37           6691         ME           Mesoproterozoic-Cambrian rocks
        38           4976         MN     Mesoproterozoic-Neoproterozoic rocks
        36           3000          M                    Mesoproterozoic rocks
        41           6798         YK       Palaeoproterozoic-Cretaceous rocks
        44           6797         YP          Palaeoproterozoic-Permian rocks
        40           5589         YE         Palaeoproterozoic-Cambrian rocks
        43           4736         YN                        Proterozoic rocks
        42           5012         YM  Palaeoproterozoic-Mesoproterozoic rocks
        39           4724          Y                  Palaeoproterozoic rocks
        1            6663         AD                  Archaean-Devonian rocks
        3            6451         AO                Archaean-Ordovician rocks
        2            6234         AM           Archaean-Mesoproterozoic rocks
        4            2961         AY         Archaean-Palaeoproterozoic rocks
        0            2960          A                           Archaean rocks

    """

    all_ages = [
        ("Qh", 11.7e3 / 1e6, 0),
        ("Qp", 2.58, 11.7e3 / 1e6),
        ("Q", 2.58, 0),
        ("Tp", 5.333, 2.58),
        ("Tm", 23.03, 5.333),
        ("To", 33.9, 23.03),
        ("Te", 56, 33.9),
        ("Ta", 66, 56),
        ("T", 66, 2.58),
        ("K", 145, 66),
        ("J", 201.4, 145),
        ("R", 251.9, 201.4),
        ("C", 298.9, 251.9),
        ("P", 358.9, 298.9),
        ("D", 419.2, 358.9),
        ("S", 443.8, 419.2),
        ("O", 485.4, 443.8),
        ("E", 538.8, 485.4),
        ("N", 1000, 538.8),
        ("M", 1600, 1000),
        ("Y", 2500, 1600),
        ("A", 4000, 2500),
    ]

    def __init__(self, db=None, **kwargs):
        if db is None:
            db = connect_to_sageodata(**kwargs)
        self.db = db

        df = self.db.query(
            """
            select
                st.strat_unit_no,
                st.subdiv_strat_unit_no as parent_strat_unit_no,
                st.map_symbol,
                st.strat_name
            from
                dhdb.st_strat_unit_vw st
            where
                st.map_symbol is not null
        """
        )
        self.strat = self.add_missing_parents(df)
        self.tlstrat = self._build_top_level_units()

    @staticmethod
    def add_missing_parents(df):
        copy = df.copy()
        copy.loc[
            copy.map_symbol.str.startswith("T")
            & (~copy.map_symbol.isin(["T", "TQ"]))
            & pd.isnull(copy.parent_strat_unit_no),
            "parent_strat_unit_no",
        ] = 3187
        copy.loc[copy.map_symbol == "JK-h", "parent_strat_unit_no"] = 4574
        copy.loc[
            copy.map_symbol.isin(["ME1", "Mt", "Mr", "Mthhdj"]), "parent_strat_unit_no"
        ] = 3000
        copy.loc[copy.map_symbol == "N-m", "parent_strat_unit_no"] = 3037
        copy.loc[copy.map_symbol == "Omy", "parent_strat_unit_no"] = 4421
        return copy

    def _build_top_level_units(self):
        units = self.db.query(
            """
            select
                st.strat_unit_no,
                st.subdiv_strat_unit_no as parent_strat_unit_no,
                st.map_symbol,
                st.strat_name
            from
                dhdb.st_strat_unit_vw st
            where
                st.subdiv_strat_unit_no is null
                and st.map_symbol is not null
        """
        )
        units = self.add_missing_parents(units)
        units = units[pd.isnull(units.parent_strat_unit_no)]

        records = []
        for idx, row in units.iterrows():
            ages = [
                (i, (sym, start, end))
                for i, (sym, start, end) in enumerate(self.all_ages)
                if sym in row.map_symbol
            ]
            min_age = 9999
            max_age = -1
            max_age_sym = ""
            min_age_sym = ""
            for i, (sym, start, end) in ages:
                if start > max_age:
                    max_age = start
                    max_age_sym = sym
                if end < min_age:
                    min_age = end
                    min_age_sym = sym
            record = row.to_dict()
            record["start"] = max_age
            record["end"] = min_age
            record["oldest_unit"] = max_age_sym
            record["youngest_unit"] = min_age_sym
            if record["start"] != -1:
                records.append(record)
        return pd.DataFrame(records).sort_values(["start", "end"])

    def _find_strat_unit_parentage(self, unit_chain):
        df = self.strat
        broadest_unit = unit_chain[0]
        finest_unit = unit_chain[-1]
        parent_units = df[df["strat_unit_no"] == broadest_unit]
        if len(parent_units) == 0:
            return unit_chain
        elif len(parent_units) == 1:
            row = parent_units.iloc[0]
            broader_unit = row.parent_strat_unit_no
            if pd.isnull(broader_unit):
                return unit_chain
            else:
                unit_chain = [broader_unit] + list(unit_chain)
                return self._find_strat_unit_parentage(unit_chain)

    def _find_strat_unit_siblings(self, st_unit_no):
        df = self.strat
        parent_units = df[df["strat_unit_no"] == st_unit_no]
        if len(parent_units) == 0:
            return []
        else:
            row = parent_units.iloc[0]
            sibling_units = df[df.parent_strat_unit_no == row.parent_strat_unit_no]
            return [u for u in sibling_units.strat_unit_no if not u == st_unit_no]

    def _find_strat_unit_next_level_children(self, st_unit_no):
        df = self.strat
        child_units = df[df["parent_strat_unit_no"] == st_unit_no]
        if len(child_units) == 0:
            return []
        else:
            return list(child_units.strat_unit_no)

    def find_strat_parentage(self, map_symbol):
        strat = self.strat
        st_unit_no = strat[strat.map_symbol == map_symbol].iloc[0].strat_unit_no
        unit_chain = self._find_strat_unit_parentage([st_unit_no])
        records = [strat[strat.strat_unit_no == s].iloc[0] for s in unit_chain]
        return pd.DataFrame(records)

    def find_strat_siblings(self, map_symbol):
        strat = self.strat
        st_unit_no = strat[strat.map_symbol == map_symbol].iloc[0].strat_unit_no
        sibling_u_nos = self._find_strat_unit_siblings(st_unit_no)
        return strat[strat.strat_unit_no.isin(sibling_u_nos)]

    def find_strat_children(self, map_symbol, levels=1):
        strat = self.strat
        assert levels == 1
        st_unit_no = strat[strat.map_symbol == map_symbol].iloc[0].strat_unit_no
        child_u_nos = self._find_strat_unit_next_level_children(st_unit_no)
        return strat[strat.strat_unit_no.isin(child_u_nos)]


class Hydrostratigraphy(StratigraphyHierarchy):
    """Tables of hydrostratigraphic units and tools for working with them.

    Args:
        db (SAGeodataConnection): default None i.e. created as needed

    Other keywords args are passed to SAGeodataConnection i.e. for
    getting into QA or Dev; production by default

    This fundamentally relies on SA Geodata being correct:

    * all aquifer monitored codes referring to hydrostrat subunits
      with [SUxx] in their description
    * all hydrostrat sub-intervals referring to subunits with
      'HS LOG ONLY' in their description

    Attributes:
        hstrat (pd.DataFrame): a table of all potential hydrostrat subunits
        aqmon (pd.DataFrame): a table of all potential aquifer monitored subunits

    The columns in strat are:

        >>> st = Hydrostratigraphy()
        >>> st.strat.info()

        >>> print(st.strat.head())

    tlstrat is:

    """

    def __init__(self, *args, **kwargs):
        super(Hydrostratigraphy, self).__init__(*args, **kwargs)

        def create_unit_name(row):
            if row.hydro_subunit_code == "" or pd.isnull(row.hydro_subunit_code):
                return row.strat_name
            else:
                return f"{row.strat_name} - {row.hydro_subunit_name}"

        def create_unit_code(row):
            if row.hydro_subunit_code == "" or pd.isnull(row.hydro_subunit_code):
                return row.map_symbol
            else:
                return f"{row.map_symbol}({row.hydro_subunit_code})"

        df = self.db.query(
            """
            select
                su.strat_unit_no,
                su.map_symbol as strat_unit,
                hsu.hydro_subunit_code,
                su.map_symbol || hsu.hydro_subunit_code as aquifer_code,
                su.strat_name,
                hsu.hydro_subunit_desc as hydro_subunit_name
            from 
                dhdb.wa_hydrostrat_subunit_vw hsu
            left join 
                dhdb.st_strat_unit_vw su on hsu.strat_unit_no = su.strat_unit_no
        """
        )
        self.hsubunit_strat = df[
            df.hydro_subunit_name.str.contains("HS LOG ONLY", regex=False)
        ]

        aqmon = df[df.hydro_subunit_name.str.contains("[SU", regex=False)]
        aqmon["linked_strat_unit_no"] = aqmon.hydro_subunit_name.str.extract(
            r"\[SU(\d{1,4})\]"
        ).astype(int)

        self.pot_aqmon = pd.merge(
            aqmon,
            self.strat.rename(
                columns={
                    "strat_unit_no": "linked_strat_unit_no",
                    "map_symbol": "linked_map_symbol",
                    "strat_name": "linked_strat_name",
                }
            )[["linked_strat_unit_no", "linked_map_symbol", "linked_strat_name"]],
            on="linked_strat_unit_no",
            how="left",
        )

        # Get hydrostrat log sub-intervals, and aquifer monitored entries.
        df2a = self.db.query(
            """
            select
                su.strat_unit_no,
                su.map_symbol,
                hsu.hydro_subunit_code,
                su.map_symbol || hsu.hydro_subunit_code as aquifer_code,
                su.strat_name,
                hsu.hydro_subunit_desc as hydro_subunit_name,
                aqmon.drillhole_no as aqmon_dh_no,
                -- aqmon.constrn_date as aqmon_date,
                hsl_int.drillhole_no as hslog_dh_no
            from 
                dhdb.wa_hydrostrat_subunit_vw hsu
            left join dhdb.st_strat_unit_vw su 
                on hsu.strat_unit_no = su.strat_unit_no
            left join dhdb.dd_dh_aquifer_mon_vw aqmon 
                on aqmon.strat_unit_no = hsu.strat_unit_no and aqmon.hydro_subunit_code = hsu.hydro_subunit_code
            left join dhdb.wa_hydrostrat_subint_vw hsl_subint
                on hsl_subint.strat_unit_no = hsu.strat_unit_no and hsl_subint.hydro_subunit_code = hsu.hydro_subunit_code
            left join dhdb.wa_hydrostrat_int_vw hsl_int
                on hsl_int.hydro_int_no = hsl_subint.hydro_int_no
            """
        )
        # Get hydrostrat log intervals made up on purely strat unit entries.
        df2b = self.db.query(
            """
            select
                su.strat_unit_no,
                su.map_symbol,
                '' as hydro_subunit_code,
                su.map_symbol as aquifer_code,
                su.strat_name,
                '' as hydro_subunit_name,
                null as aqmon_dh_no,
                hsl_int.drillhole_no as hslog_dh_no
            from
                dhdb.wa_hydrostrat_int_vw hsl_int
            left join dhdb.st_strat_unit_vw su
                on hsl_int.strat_unit_no = su.strat_unit_no
        """
        )
        df2b["hydro_subunit_code"] = ""
        df2b["hydro_subunit_name"] = "HS LOG ONLY"
        df2 = pd.concat([df2a, df2b])
        df2 = df2.sort_values(
            ["map_symbol", "hydro_subunit_code", "hydro_subunit_name"]
        )
        df2_summ = (
            df2.groupby(
                [
                    "map_symbol",
                    "hydro_subunit_code",
                    "aquifer_code",
                    "strat_name",
                    "hydro_subunit_name",
                ]
            )
            .agg(
                count_aqmon=("aqmon_dh_no", lambda dh_nos: dh_nos.dropna().nunique()),
                count_hslog=("hslog_dh_no", lambda dh_nos: dh_nos.dropna().nunique()),
            )
            .reset_index()
        )

        self.hslog_use = (
            df2[~df2.hslog_dh_no.isnull()]
            .drop(["aquifer_code", "aqmon_dh_no"], axis=1)
            .drop_duplicates()
        )
        self.aqmon_use = (
            df2[~df2.aqmon_dh_no.isnull()]
            .drop(["hslog_dh_no"], axis=1)
            .drop_duplicates()
        )

        self.hslog_summ_use = df2_summ[df2_summ.count_hslog > 0].drop(
            ["aquifer_code", "count_aqmon"], axis=1
        )
        self.aqmon_summ_use = df2_summ[df2_summ.count_aqmon > 0].drop(
            ["count_hslog"], axis=1
        )

        self.hslog_use["unit_code"] = self.hslog_use.apply(create_unit_code, axis=1)
        self.hslog_summ_use["unit_code"] = self.hslog_summ_use.apply(
            create_unit_code, axis=1
        )

        hslog_valid = self.hslog_use.hydro_subunit_name.str.contains(
            "HS LOG ONLY", regex=False
        )
        self.hslog_errors = self.hslog_use[~hslog_valid]
        self.hslog_use = self.hslog_use[hslog_valid]

        self.hslog_summ_use = self.hslog_summ_use[
            self.hslog_summ_use.hydro_subunit_name.str.contains(
                "HS LOG ONLY", regex=False
            )
        ]

        aqmon_valid = self.aqmon_use.hydro_subunit_name.str.contains("SU", regex=False)
        self.aqmon_errors = self.aqmon_use[~aqmon_valid]
        self.aqmon_use = self.aqmon_use[aqmon_valid]

        self.aqmon_summ_use = self.aqmon_summ_use[
            self.aqmon_summ_use.hydro_subunit_name.str.contains("[SU", regex=False)
        ]

        self.aqmon_use["linked_strat_unit_no"] = (
            self.aqmon_use.hydro_subunit_name.str.extract(r"\[SU(\d{1,4})\]").astype(
                int
            )
        )
        self.aqmon_use = pd.merge(
            self.aqmon_use,
            self.strat.rename(
                columns={
                    "strat_unit_no": "linked_strat_unit_no",
                    "map_symbol": "linked_map_symbol",
                    "strat_name": "linked_strat_name",
                }
            )[["linked_strat_unit_no", "linked_map_symbol", "linked_strat_name"]],
            on="linked_strat_unit_no",
            how="left",
        )

        self.aqmon_summ_use["linked_strat_unit_no"] = (
            self.aqmon_summ_use.hydro_subunit_name.str.extract(
                r"\[SU(\d{1,4})\]"
            ).astype(int)
        )
        self.aqmon_summ_use = pd.merge(
            self.aqmon_summ_use,
            self.strat.rename(
                columns={
                    "strat_unit_no": "linked_strat_unit_no",
                    "map_symbol": "linked_map_symbol",
                    "strat_name": "linked_strat_name",
                }
            )[["linked_strat_unit_no", "linked_map_symbol", "linked_strat_name"]],
            on="linked_strat_unit_no",
            how="left",
        )

        self.aqmon_use = self.aqmon_use.rename(
            columns={"hydro_subunit_name": "aquifer_name"}
        )
        self.aqmon_summ_use = self.aqmon_summ_use.rename(
            columns={"hydro_subunit_name": "aquifer_name"}
        )

        hslog_units = self.strat[["strat_unit_no", "map_symbol", "strat_name"]]
        hslog_subunits = pd.merge(
            self.strat[["strat_unit_no", "map_symbol", "strat_name"]],
            self.hsubunit_strat[
                ["strat_unit_no", "hydro_subunit_code", "hydro_subunit_name"]
            ],
            on="strat_unit_no",
            how="right",
        )
        pot_hlog_units = pd.concat([hslog_units, hslog_subunits])
        pot_hlog_units["hydro_subunit_code"] = pot_hlog_units[
            "hydro_subunit_code"
        ].fillna("")
        pot_hlog_units["hydro_subunit_name"] = pot_hlog_units[
            "hydro_subunit_name"
        ].fillna("")
        pot_hlog_units["unit_name"] = pot_hlog_units.apply(create_unit_name, axis=1)
        pot_hlog_units["unit_code"] = pot_hlog_units.apply(create_unit_code, axis=1)
        pot_hlog_units = pot_hlog_units.sort_values("unit_code")
        pot_hlog_units = pot_hlog_units[
            [
                "strat_unit_no",
                "map_symbol",
                "strat_name",
                "hydro_subunit_code",
                "hydro_subunit_name",
                "unit_code",
                # "unit_name",
            ]
        ]

        h_int_df = self.db.query(
            """
            select
                int.drillhole_no as dh_no,
                int.strat_unit_no
            from dhdb.wa_hydrostrat_int_vw int
        """
        )
        actual_hlog_units = pot_hlog_units[
            pot_hlog_units.strat_unit_no.isin(h_int_df.strat_unit_no)
        ]

        self.pot_hlog_units = pot_hlog_units
        self.actual_hlog_units = actual_hlog_units

        self.aq_codes = pd.merge(
            self.pot_aqmon,
            self.aqmon_summ_use[["aquifer_code", "count_aqmon"]],
            on="aquifer_code",
            how="left",
        )
        self.aq_codes = self.aq_codes[
            [
                "strat_unit_no",
                "strat_unit",
                "strat_name",
                "hydro_subunit_code",
                "aquifer_code",
                "count_aqmon",
                "hydro_subunit_name",
                "linked_strat_unit_no",
                "linked_map_symbol",
                "linked_strat_name",
            ]
        ]
        self.hlog_codes = pd.merge(
            self.pot_hlog_units,
            self.hslog_summ_use[["unit_code", "count_hslog"]],
            on="unit_code",
            how="left",
        )
        self.hlog_codes = self.hlog_codes[
            (self.hlog_codes.hydro_subunit_code != "")
            | (self.hlog_codes.count_hslog > 0)
        ]
        self.hlog_codes = self.hlog_codes[
            [
                "strat_unit_no",
                "map_symbol",
                "strat_name",
                "unit_code",
                "count_hslog",
                "hydro_subunit_code",
                "hydro_subunit_name",
            ]
        ]


class ProductionZoneData:
    """Class to make it easier to use production zone (PZ) data from SA Geodata.
    PZ data is basically the riser, screen, slotted section, blank section, sump,
    and/or open-hole data records.

    It is complicated because of the presence of S-type records (survey events) which
    largely measure the depth of a borehole, and multiple records, when usually we
    want the most recent current construction.

    This class provides a way to automatically generate a single record which has
    the max and min depth of the open interval, ignoring the rare situation where
    there may be blanks within that open interval.

    Args:
        wells: list of drillhole numbers or a dataframe with 'dh_no'
        db (SAGeodataConnection): will create a new connection if not supplied
        index_id (str): well ID column to use as the index for pzone attribute.

    Attributes:
        pzones (pd.DataFrame): the original data obtained via db.production_zones(dh_nos)
        events (pd.DataFrame): only construction event PZ data with a completion date
        most_recent_event (pd.DataFrame): the most recent construction event PZ data
        open_pzone_intervals (pd.DataFrame): the open intervals (screen, slots, open hole) from the
            most recent construction event PZ data
        pzone (pd.DataFrame): the maximum extent of open intervals - note this dataframe
            has the index_id argument set as the index, and it is guaranteed to have only
            one record/row for each well.

    Note the attributes are all dataframes because the object can be used for one or
    more wells.

    Example usage

    .. code-block::

        >>> import dew_gwdata as gd
        >>> db = gd.sageodata()
        >>> wells = db.find_wells('YAT060 YAT115')
        >>> pz = db.ProductionZoneData(wells, index_id='obs_no')
        >>> pz.pzone.loc['YAT060']
        well_id                             YAT060
        dh_no                                58443
        unit_hyphen                     6628-11474
        unit_long                        662811474
        completion_date        1979-03-14 00:00:00
        open_depth_from_min                   15.0
        open_depth_to_max                     21.0
        open_types                              SC
        open_extent                   (15.0, 21.0)
        Name: YAT060, dtype: object

    """

    def __init__(self, wells, db=None, index_id="obs_no"):
        if db is None:
            db = connect_to_sageodata()

        pzones = db.production_zones(wells)
        events = pzones[
            (pzones.event_type == "C") & (~pd.isnull(pzones.completion_date))
        ]
        most_recent_event = events.groupby("dh_no", group_keys=False).apply(
            lambda grp: grp[grp.completion_date == grp.completion_date.max()]
        )
        open_pzone_intervals = most_recent_event[
            most_recent_event.pzone_type.isin(["S", "SC", "OH", "WS"])
        ]
        open_pzone_intervals.loc[pd.isnull(open_pzone_intervals.obs_no), "obs_no"] = (
            "NA"
        )
        pzone = (
            open_pzone_intervals.groupby(
                [
                    "well_id",
                    "obs_no",
                    "dh_no",
                    "unit_hyphen",
                    "unit_long",
                    "completion_date",
                ]
            )
            .agg(
                open_depth_from_min=("depth_from", "min"),
                open_depth_to_max=("depth_to", "max"),
                open_types=("pzone_type", lambda ptypes: " ".join(ptypes)),
            )
            .reset_index()
        )
        pzone["open_extent"] = pzone.apply(
            lambda row: (row.open_depth_from_min, row.open_depth_to_max), axis=1
        )
        self.pzones = pzones
        self.events = events
        self.most_recent_event = most_recent_event
        self.open_pzone_intervals = open_pzone_intervals
        self.pzone = pzone

        self.set_index(index_id)

    def set_index(self, id_col):
        """Change the well ID column used as the index for the attribute pzone.

        Args:
            id_col (str): either 'unit_long', 'unit_hyphen', 'obs_no', or 'well_id'

        """
        assert id_col in ("unit_long", "unit_hyphen", "obs_no", "well_id")
        self.pzone = self.pzone.set_index(id_col)


def get_dem_elev(xy_coords, crs="epsg:7844"):
    """Obtain a rapid elevation value from DEW EGIS DEMs.

    Args:
        xy_coords: an array of x, y tuples for each location
        crs: coordinate system of tuples. Longitude and latitude by default.
            SA Lambert GDA2020 is "epsg:8059". GDA2020 zones are
            "epsg:7853" and "epsg:7854" respectively.

    Returns:
        gpd.GeoDataFrame: a dataframe with columns "geometry",
        "x", "y", "elev", and "elev_source"

    See source code for the DEMS in use. Currently they are sourced
    from EGIS and are:

    - DEM_NASA_30M (i.e. the SRTM)
    - DEM_ADHILLS_10M
    - DEM_SE_10M

    The most accurate available is used

    """

    layer_bounds = {
        "R:\DFW_CBD\Geophyslogs\giscache\dem_nasa_30m.tif": {
            "left": 29664.586230052802,
            "bottom": 1140353.10508565,
            "right": 1970394.58623005,
            "top": 2829983.10508565,
        },
        "R:\DFW_CBD\Geophyslogs\giscache\dem_adhills_10m.tif": {
            "left": 1279784.32845606,
            "bottom": 1584673.99189635,
            "right": 1387694.32845606,
            "top": 1737933.99189635,
        },
        "R:\DFW_CBD\Geophyslogs\giscache\dem_se_10m.tif": {
            "left": 1371606.553399,
            "bottom": 1311986.42128288,
            "right": 1541946.553399,
            "top": 1608656.42128288,
        },
    }

    x = [val[0] for val in xy_coords]
    y = [val[1] for val in xy_coords]
    pts_original = gpd.points_from_xy(x, y, crs=crs)
    pts = gpd.GeoSeries(pts_original.to_crs("epsg:8059")).to_frame(name="geometry")
    pts["x"] = pts.geometry.x
    pts["y"] = pts.geometry.y
    for file, bounds in layer_bounds.items():
        file = Path(file)
        pts_subset = pts[
            (pts.x >= bounds["left"])
            & (pts.x <= bounds["right"])
            & (pts.y >= bounds["bottom"])
            & (pts.y <= bounds["top"])
        ]
        with rasterio.open(file) as raster:
            elevs = raster.sample(pts_subset[["x", "y"]].values)
            pts_subset["elev"] = [
                elev[0] if elev[0] != -9999 else pd.NA for elev in elevs
            ]
            pts_subset["elev_source"] = file.stem
        pts_subset = pts_subset.dropna(subset=["elev"], how="any")
        pts.loc[pts_subset.index, ["elev", "elev_source"]] = pts_subset[
            ["elev", "elev_source"]
        ]
    return pts


def depth_to_elev(df, db=None, precision=1):
    """Converts any depth columns to elevations in a new column.

    Args:
        df (pd.DataFrame): any table - it should have "latitude" and "longitude"
            columns or "dh_no" (so that the location can be looked up).
        db (optional SAGeodataConnection): only used if we need to look up
            the location via "dh_no" field.

    Returns:
        pd.DataFrame: the same dataframe as input with additional columns:

        - "elev" - from :func:`dew_gwdata.get_dem_elev`
        - "elev_source" - from :func:`dew_gwdata.get_dem_elev`
        - anything in the original dataframe with "depth" will have "_mahd"
          appended and the value in the depth column converted to "elev"
        - some special cases like "casing_at_test" is identified as a depth
        - "rswl" - any rows where "swl" is populated by "rswl" is not will be
          filled in appropriately.

    .. warning::

        This function does not look at the elevation data that is
        already in SA Geodata! It purely uses the elevation rasters used
        by :func:`dew_gwdata.get_dem_elev`. Although this is fine for most
        purposes, it may lead to some confusion.

    """
    if len(df) == 0:
        return pd.DataFrame(columns=list(df.columns) + ["elev", "elev_source"])
    if "latitude" in df.columns and "longitude" in df.columns:
        xy_coords = df[["longitude", "latitude"]].values
        crs = "epsg:7844"
    elif "dh_no" in df.columns:
        if db is None:
            db = connect_to_sageodata()
        details = db.drillhole_details(df.dh_no)
        df_for_coords = pd.merge(df, details, on="dh_no", how="left")
        xy_coords = df_for_coords[["longitude", "latitude"]].values
        crs = "epsg:7844"

    elev_df = get_dem_elev(xy_coords, crs)
    elev_df.index = df.index

    logger.warning(str(elev_df))

    df_result = pd.merge(
        df,
        elev_df[["elev", "elev_source"]],
        left_index=True,
        right_index=True,
        how="left",
    )
    for col in df_result.columns:
        new_col = None
        if "depth" in col or col in ("casing_at_test",):
            new_col = col + "_mahd"
        if new_col and "greater" in col:
            new_col = None
        if new_col and "date" in col:
            new_col = None
        if new_col:
            try:
                df_result[new_col] = pd.to_numeric(
                    df_result.elev - df_result[col], errors="coerce"
                )
                df_result[new_col] = df_result[new_col].round(precision)
            except TypeError as e:
                raise Exception(f"Column '{new_col}' may not be an elevation") from e
    if "rswl" in df_result.columns and "swl" in df_result.columns:
        df_result.loc[pd.isnull(df_result.rswl), "rswl"] = (
            df_result.elev - df_result.swl
        )
    return df_result


def add_elev_cols(df, dh_no, ignore_empty=True, precision=1):
    orig_cols = [str(c) for c in df.columns]
    df["dh_no"] = dh_no
    df2 = depth_to_elev(df, precision=precision)
    df = df[orig_cols]
    for col in df2.columns:
        if "_mahd" in col:
            orig_col = col.replace("_mahd", "")
            df.insert(list(df.columns).index(orig_col) + 1, col, df2[col].round(3))
    if ignore_empty:
        df = df.replace("", pd.NA).dropna(how="all", axis=1)
    df = df[[c for c in df.columns if not c in ("elev", "elev_source")]]
    return df


def locate_points_in_suburbs(gdf):
    suburbs_layer = gpd.read_file(
        Path(r"p:\projects_gw\state\giscache\suburbs_fast_7844.gpkg"),
        layer="suburbs_fast_7844",
    )
    values = []
    for idx, point_location in gdf.iterrows():
        all_matches = suburbs_layer.geometry.contains(point_location.geometry)
        true_matches = all_matches[all_matches == True]
        if len(true_matches.dropna()):
            suburb = suburbs_layer.loc[true_matches.dropna().index[0]].SUBURB
        else:
            suburb = ""
        values.append(suburb)
    return pd.Series(values, index=gdf.index)


def locate_wells_in_suburbs(wells_df, db=None):
    df = wells_df.copy(deep=True)
    assert "dh_no" in df.columns
    if not (
        "latitude" in df.columns and "longitude" in df.columns and "dh_no" in df.columns
    ):
        if db is None:
            db = connect_to_sageodata()
        well_details = db.wells_summary(df.dh_no.unique())
        df["latitude"] = df.dh_no.map(well_details.set_index("dh_no").latitude)
        df["longitude"] = df.dh_no.map(well_details.set_index("dh_no").longitude)
    gdf = gpd.GeoDataFrame(
        df[["dh_no"]],
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"], crs="epsg:7844"),
    )
    gdf["suburb"] = locate_points_in_suburbs(gdf)
    result = gdf.suburb
    return result


def normalise_and_clean_logger_data(df):
    """Normalise and clean logger data.

    Args:
        df (pd.DataFrame): the index should be the timestamp.

    This function:

    1. Removes duplicate timestamp rows
    2. Removes any rows with null values
    3. Renames known columns (e.g. AQ parameters are renamed to simple versions)

    See source for details.

    """
    # Drop repeat measurements at the same timestamp
    df = df[~df.index.duplicated(keep="first")]

    df = df.rename(
        columns={
            "Depth to Water (m)": "dtw",
            "Depth to Water": "dtw",
            "SWL (m)": "swl",
            "SWL": "swl",
            "RSWL (m)": "rswl",
            "RSWL": "rswl",
            "EC Corr (uS/cm@25C)": "ec",
            "EC Corr": "ec",
            "TDS from EC (mg/l)": "tds",
            "TDS from EC": "tds",
            "Grade Code": "grade",
            "Approval Level": "approval",
        }
    )

    param_cols = ["dtw", "swl", "rswl", "ec", "tds"]

    # Drop null data points
    df = df.dropna(subset=[c for c in param_cols if c in df.columns], how="any")

    df.index.name = "timestamp"
    return df


def resample_logger_data(
    df,
    freq="6H",
    max_gap_days=1,
    keep_grades=(1, 20, 30),
):
    """Resample and 'chunk' logger data.

    Args:
        df (pandas.DataFrame): the timestamp should be set as the index, so for
            example if you have "obs_date" or "timestamp" containing datetime
            objects as a column, you need to set it as the index with
            ``df.set_index("timestamp")``.
        freq (str): either "as-recorded" (data points as they exist) or a pandas
            frequency string e.g "6H", "2d" etc.
        max_gap_days (float): maximum allowable gap between data points in days
        keep_grades (tuple): grades to keep. 1 = telemetry, 10 = water level outside
            of recordable range, 15 = poor which GW Team uses to mean "unusable",
            20 = fair, 30 = good. Use None to keep all measurements.

    Returns:
        list of pd.DataFrame: each df is guaranteed to have no gaps in the
        timestamp column > max_gap_days. The columns of each dataframe are:

            - "timestamp": pd.Timestamp - tz-aware with timezone UTC+09:30 i.e. ACST
            - the parameter, titled either "dtw", "swl", "rswl", "ec", or "tds"
            - "chunk_id" - this integer increments from 0, 1, 2 depending on how
                many gaps were found in the data (gaps > max_gap_days above)

    """
    if "grade" in df and keep_grades:
        df = df[df.grade.isin(keep_grades)]

    final_dfs = []
    if len(df):
        # Break into chunks
        df["chunk_id"] = (
            ~df.index.to_series().diff().dt.days.div(max_gap_days, fill_value=0).lt(2)
        ).cumsum()
        dfs = {}
        for i, group in df.groupby("chunk_id"):
            dfs.update(dict([(str(i), group)]))

        if freq == "as-recorded":
            final_dfs = [chunk_df for chunk_df in dfs.values()]
        else:
            for chunk_id, df in dfs.items():
                # Re-sample to requested frequency
                old_index = df.index
                new_index = pd.date_range(old_index.min(), old_index.max(), freq=freq)
                new_df = (
                    df.reindex(old_index.union(new_index))
                    .interpolate("index")
                    .reindex(new_index)
                )
                new_df.index.name = old_index.name
                final_dfs.append(new_df)

    return [df.reset_index() for df in final_dfs]


def get_logger_interval_details(dfs):
    """Get details of logger data dataset intervals.

    Args:
        dfs (pd.DataFrame): a list of logger datasets. Each dataset
            should be continuous in the column "timestamp" with a
            consistent frequency and no null data record.

    Returns:
        pd.DataFrame: with columns:

            - dataset_length (integer)
            - start_timestamp (pd.Timestamp)
            - finish_timestamp (pd.Timestamp)
            - span_timedelta (pd.Timedelta)
            - span_days (float): total days
            - span_years (float): total years
            - freq_timedelta (pd.Timedelta)
            - freq_pandas (str): e.g. "24H" - may be null for single-point
              datasets

    """
    records = []
    for df in dfs:
        record = {}
        df = df.sort_values("timestamp")
        record["dataset_length"] = len(df)
        record["start_timestamp"] = df.timestamp.iloc[0]
        record["finish_timestamp"] = df.timestamp.iloc[-1]
        span = df.timestamp.iloc[-1] - df.timestamp.iloc[0]
        record["span_timedelta"] = span
        record["span_days"] = span.total_seconds() / 60 / 60 / 24
        record["span_years"] = record["span_days"] / 365.25
        if len(df) > 1:
            freqs = df.timestamp.diff()
            unique_freq = freqs.unique()
            if len(unique_freq) == 1:
                freq = list(unique_freq)[0]
            else:
                freq = freqs.median()
            freq_hours = freq.total_seconds() / 60 / 60
            freq_days = freq.total_seconds() / 60 / 60 / 24
            if freq_days > 1 and freq_days == int(freq_days):
                freq_str = f"{freq_days:.0f}d"
            elif freq_hours == int(freq_hours):
                freq_str = f"{freq_hours:.0f}H"
            else:
                freq_str = None
        else:
            freq = pd.NA
            freq_str = None
        record["freq_timedelta"] = freq
        record["freq_pandas"] = freq_str
        records.append(record)
    return pd.DataFrame(records)


def join_logger_data_intervals(
    dfs,
    method="single-null",
    param_if_empty="swl",
    copy_params_for=(
        "well_id",
        "unit_hyphen",
        "unit_long",
        "dh_no",
        "dh_name",
        "obs_no",
    ),
):
    """Join a sequence of continuous logger datasets into one.

    Args:
        dfs (list of pd.DataFrames)
        method (str): "single-null" is the only option at the moment - see below
        param_if_empty (str): if there are no entries in *dfs*, what param
            should be used to create the empty dataframe which is returned?
        copy_params_for (sequence of str): if method == "single-null", these
            columns will have their values copied from the preceding dataframe
            assuming that the timestamp of the succeeding dataframe is greater
            than the preceding. This should mean that when
            multiple wells are included in dfs, everything works as intended
            and when ``df.groupby('unit_hyphen').plot(x='timestamp', y='swl')``
            is used, everything works as intended.

    For method == "single-null", a single record with pd.NA
    values is added halfway between each continuous dataset.
    This plots nicely in matplotlib.

    Returns:
        pd.DataFrame: with the same columns as dfs, but NaN values in the
        relevant parameter columns, means the matplotlib should plot with
        broken lines.

    """
    if len(dfs) == 0:
        return pd.DataFrame(
            columns=[
                "timestamp",
                param_if_empty,
                "grade",
                "approval",
                "qualifier",
                "chunk_id",
            ]
        )
    if method == "single-null":
        columns = dfs[0].columns
        new_list = [dfs[0]]
        for df in dfs[1:]:
            record = {}
            preceding_ts = new_list[-1]["timestamp"].iloc[-1]
            succeeding_ts = df["timestamp"].iloc[0]
            new_ts = preceding_ts + (succeeding_ts - preceding_ts) / 2
            record = {k: np.nan for k in columns}
            if succeeding_ts > preceding_ts:
                for col in copy_params_for:
                    if col in record:
                        record[col] = dfs[0][col].iloc[0]
            record["timestamp"] = new_ts
            new_list.append(pd.DataFrame([pd.Series(record)]))
            new_list.append(df)
    else:
        raise KeyError(f"method '{method}' not understood")
    return pd.concat(new_list).reset_index()


def convert_aq_param(param):
    """Convert between parameter names, in either direction.

    The parameters are:

    - "Depth to Water", "dtw"
    - "SWL", "swl",
    - "RSWL", "rswl"
    - "EC Corr", "ec"
    - "TDS from EC", "tds"

    These are effectively the long and short parameter names
    configured in our Aquarius system.

    """
    mapping = {
        "Depth to Water": "dtw",
        "SWL": "swl",
        "RSWL": "rswl",
        "EC Corr": "ec",
        "TDS from EC": "tds",
        "dtw": "Depth to Water",
        "swl": "SWL",
        "rswl": "RSWL",
        "ec": "EC Corr",
        "tds": "TDS from EC",
    }
    return mapping[param]


def get_combined_water_level_dataset(
    dh_nos,
    db=None,
    param="swl",
    sagd_env="prod",
    start=None,
    finish=None,
    freq="5d",
    max_gap_days=550,
    keep_grades=(1, 20, 30),
    aq_env="prod",
):
    """Fetch and combine manual and logger water level datasets.

    Args:
        dh_nos (sequence of int): drillhole numbers.
        db (SAGeodataConnection object): optional
        param (str): either "dtw", "swl" or "rswl"
        sagd_env (str): either "prod", "test", or "dev"
        start (pd.Timestamp in ACST): first time to retrieve data from
            e.g. to provide 9am on the 17th May 2023,
            use ``start=gd.timestamp_acst("2023-05-17 09:00")``
        finish (pd.Timestamp in ACST): last time to retrieve data from.
        freq (str): either "as-recorded" (data points as they exist) or a pandas
            frequency string e.g "6h" (hours), "2d" (days), "1w" (weeks).
        max_gap_days (float): maximum allowable gap between data points in days
        keep_grades (tuple): grades to keep. 1 = telemetry, 10 = water level outside
            of recordable range, 15 = poor which GW Team uses to mean "unusable",
            20 = fair, 30 = good. Use None to keep all measurements.
        aq_env (str): either "dev", "qa", or "prod"

    Returns:
        sequence of pd.DataFrame: the function returns a list of dataframes,
        given the value of max_gap_days, i.e. if there is a gap in data, it
        breaks the dataset into separate dataframes at the point. If you don't
        care about gaps in data, you can either set max_gap_days to an
        impossibly large value (100,000), or you can leave it to the default
        and undo the gaps by using ``pd.concat`` on the returned sequence.

    :func:`dew_gwdata.aquarius_ts.DEWAquarius.fetch_timeseries_data` is used
    in the background to fetch the data.

    """
    if db is None:
        db = connect_to_sageodata(service_name=sagd_env)

    from .aquarius_ts import DEWAquarius

    aq = DEWAquarius(env=aq_env)

    summ = db.wells_summary(dh_nos)
    unit_hyphens = list(summ.unit_hyphen.unique())
    aq_dsets = aq.fetch_locations_timeseries_metadata(unit_hyphens)
    aq_dsets = aq_dsets[aq_dsets.param == convert_aq_param(param)].rename(
        columns={"ts_id": "dset_name"}
    )

    cols = [
        "dh_no",
        "unit_hyphen",
        "timestamp",
        param,
        "grade",
        "comments",
        "database",
        "approval",
        "qualifier",
        "unit_long",
        "obs_no",
        "dh_name",
    ]

    dfs = []
    for idx, row in aq_dsets.iterrows():
        row_dfs = aq.fetch_timeseries_data(
            row.loc_id,
            param=param,
            freq=freq,
            keep_grades=keep_grades,
            start=start,
            finish=finish,
        )
        df = join_logger_data_intervals(row_dfs, param_if_empty=param)
        df["unit_hyphen"] = row.loc_id
        df["database"] = "AQTS"
        df["comments"] = ""
        df = pd.merge(
            df,
            summ[["dh_no", "unit_hyphen", "unit_long", "obs_no", "dh_name"]],
            left_on="unit_hyphen",
            right_on="unit_hyphen",
            how="left",
        )

        df = df[cols]
        dfs.append(df)

    manual = db.water_levels(dh_nos)
    manual = manual.rename(columns={"obs_date": "timestamp"})
    if len(manual) > 0:
        manual["timestamp"] = manual.timestamp.dt.tz_localize(
            datetime.timezone(offset=datetime.timedelta(hours=9.5))
        )
    if start is None:
        start = manual.timestamp.min()
    if finish is None:
        finish = manual.timestamp.max()
    manual = manual[(manual.timestamp >= start) & (manual.timestamp <= finish)]
    manual["grade"] = 30
    manual.loc[manual.anomalous_ind == "Y", "grade"] = (
        15  # TODO: this should be in the SQL for water_levels*.sql
    )
    manual["approval"] = "Approved"
    manual["qualifier"] = ""
    manual["chunk_id"] = -1
    manual["database"] = "SAGD"
    manual = manual[cols]

    dfs.append(manual)

    df = pd.concat(dfs).sort_values(["unit_hyphen", "timestamp"])
    if keep_grades:
        df = df[df.grade.isin(keep_grades)]

    for db_value in df.database.unique():
        df[f"{param}-{db_value}"] = "null"
    for db_value in df.database.unique():
        idx = df.database == db_value
        df.loc[idx, f"{param}-{db_value}"] = df.loc[idx, param]

    # Break with a max gap days style thing.
    dfs = resample_logger_data(
        df.set_index("timestamp"),
        freq="as-recorded",
        max_gap_days=max_gap_days,
        keep_grades=None,
    )

    return dfs


def current_ref_height(df):
    """Return a current reference height for the well.

    Args:
        df (pd.DataFrame): elevation survey data from SA Geodata. Must have columns
            "elev_date", "applied_date", "ground_elev", "ref_elev" and "ref_height".

    Firstly, try to calculate ref height from records that include both a ref and ground
    elevation, and use the most recently applied, or added, record.

    If there are no calculated records, revert to the same process using manually entered
    reference height values.

    If no records, return pd.NA.

    Ideally it can be applied to obtain a pandas series indexed by wells via groupby e.g.

    ```
    >>> import dew_gwdata as gd
    >>> db = gd.sageodata()
    >>> wells = db.find_wells("FLN8, FLN25, FLN35, FLN56, FLN57")
    >>> elev = db.elevation_surveys(wells)
    >>> ref_heights = elev.groupby("obs_no").apply(gd.current_ref_height)
    >>> ref_heights
    obs_no
    FLN008    0.380
    FLN025    0.380
    FLN035    0.000
    FLN056    0.000
    FLN057    0.860
    ```

    """
    df.loc[
        (~pd.isnull(df.ground_elev)) & (~pd.isnull(df.ref_elev)), "ref_height_calc"
    ] = (df.ref_elev - df.ground_elev)
    df_calc = df[~pd.isnull(df.ref_height_calc)]
    if len(df_calc):
        applied = df_calc.dropna(subset=["applied_date"]).sort_values("applied_date")
        if len(applied):
            return applied.ref_height_calc.iloc[-1]
        else:
            return df_calc.sort_values("elev_date").ref_height_calc.iloc[-1]
    else:
        df_manual = df[~pd.isnull(df.ref_height)]
        if len(df_manual):
            applied = df_manual.dropna(subset=["applied_date"]).sort_values(
                "applied_date"
            )
            if len(applied):
                return applied.ref_height.iloc[-1]
            else:
                return df_manual.sort_values("elev_date").ref_height.iloc[-1]
    return pd.NA


def auto_dwcr(file_obj, dh_no, completion_no=None, db=None):
    if db is None:
        db = connect_to_sageodata()

    cevents = db.construction_events([dh_no])

    if completion_no is None:
        completion_no = cevents.completion_no.iloc[0]

    cevent = cevents[cevents.completion_no == completion_no].iloc[0]

    drill = db.drilled_intervals([dh_no]).query(f"completion_no == {completion_no}")
    case = db.casing_strings([dh_no]).query(f"completion_no == {completion_no}")
    seal = db.casing_seals([dh_no]).query(f"completion_no == {completion_no}")
    pz = db.production_zones([dh_no]).query(f"completion_no == {completion_no}")
    dlog = db.drillers_logs([dh_no]).query(f"completion_no == {completion_no}")
    devl = db.well_development([dh_no]).query(f"completion_no == {completion_no}")
    gsp = db.gravel_packing([dh_no]).query(f"completion_no == {completion_no}")
    seals = db.casing_seals([dh_no]).query(f"completion_no == {completion_no}")
    wcut = db.water_cuts_by_completion([completion_no])
    wl = db.water_levels([dh_no])
    wl = wl[wl.obs_date == cevent.completion_date]
    if len(wl) > 1:
        wl = wl[wl.measured_during == "D"]
    if len(wl) >= 1:
        wl = wl.iloc[0]
        final_wl = wl.swl
    else:
        final_wl = 0
    yields = db.well_yields([dh_no])
    yields = yields[yields.obs_date == cevent.completion_date]
    if len(yields):
        final_yield = yields.sort_values("well_yield").well_yield.iloc[-1]
    else:
        final_yield = 0

    permits = db.permit_details([cevent.permit_no_only])

    if len(permits):
        permit = permits.iloc[0]
    else:
        permit = pd.DataFrame(columns=permits.columns)

    reader = pypdf.PdfReader(Path(__file__).parent / "dwcr_form.pdf")
    writer = pypdf.PdfWriter()
    page = reader.pages[0]
    fields = reader.get_fields()
    writer.append(reader)

    def exists(value):
        if not value:
            return False
        try:
            if np.isnan(value):
                return False
        except:
            pass
        return True

    def use(value, fmt=None, accept_zero=False):
        if not value:
            if accept_zero and value == 0:
                pass
            else:
                return ""
        try:
            if np.isnan(value):
                return ""
        except:
            pass
        if fmt:
            return f"{value:{fmt}}"
        else:
            return str(value)

    def get_permit(pn):
        if pn:
            pn_str = f"{pn:6.0f}"
            return pn_str
        else:
            return "      "

    field_values = {
        "permit_no_digit1": get_permit(cevent.permit_no_only)[0],
        "permit_no_digit2": get_permit(cevent.permit_no_only)[1],
        "permit_no_digit3": get_permit(cevent.permit_no_only)[2],
        "permit_no_digit4": get_permit(cevent.permit_no_only)[3],
        "permit_no_digit5": get_permit(cevent.permit_no_only)[4],
        "permit_no_digit6": get_permit(cevent.permit_no_only)[5],
        "site_code": use(cevent.site_extension),
        "driller_name": use(
            cevent.driller_name
        ),  # if exists(cevent.driller_name) else "",
        "easting": f"{cevent.easting:.0f}",
        "northing": f"{cevent.northing:.0f}",
        "well_name": use(cevent.dh_name),
        "date_completed": (
            cevent.completion_date.strftime("%d/%m/%Y")
            if cevent.completion_date
            else ""
        ),
        "checkbox_rehabilitated": "/On" if cevent.rehabilitated == "Y" else "/Off",
        "checkbox_backfilled": "/On" if cevent.backfilled == "Y" else "/Off",
        "checkbox_replacement": "/On" if cevent.replacement == "Y" else "/Off",
        # "replaced_unit_hyphen": "",
        "checkbox_new": "/On" if cevent.orig_flag == "Y" else "/Off",
        "checkbox_existing": "/Off" if cevent.orig_flag != "N" else "/On",
        "existing_unit_hyphen": cevent.unit_hyphen if cevent.orig_flag == "N" else "",
        "site_zone52": "/On" if cevent.zone == 52 else "/Off",
        "site_zone53": "/On" if cevent.zone == 53 else "/Off",
        "site_zone54": "/On" if cevent.zone == 54 else "/Off",
        "max_drilled_depth": use(cevent.total_depth, fmt=".2f"),
        "final_depth": use(cevent.final_depth, fmt=".2f", accept_zero=True),
        "final_swl": use(final_wl, fmt=".2f", accept_zero=True),
        "final_yield": use(final_yield, fmt=".2f"),
        "unit_hyphen": use(cevent.unit_hyphen),
        "header": f"This was automatically generated from SA Geodata at {datetime.datetime.now()}",
    }

    for i, (idx, drow) in enumerate(drill.iterrows()):
        field_values[f"dr{i}_from"] = use(drow.depth_from, fmt=".2f", accept_zero=True)
        field_values[f"dr{i}_to"] = use(drow.depth_to, fmt=".2f")
        field_values[f"dr{i}_diam"] = use(drow.diam, fmt=".0f")
        field_values[f"dr{i}_method"] = drow.drill_method

    for i, (idx, row) in enumerate(wcut.iterrows()):
        field_values[f"wc{i}_date"] = (
            row.obs_date.strftime("%d/%m/%Y") if row.obs_date else ""
        )
        field_values[f"wc{i}_from"] = use(row.depth_from, fmt=".2f", accept_zero=True)
        field_values[f"wc{i}_to"] = use(row.depth_to, fmt=".2f")
        field_values[f"wc{i}_swl"] = use(row.swl, fmt=".2f")
        field_values[f"wc{i}_yield"] = use(row["yield"], fmt=".1f")
        field_values[f"wc{i}_depth_at_test"] = use(row.depth_at_test, fmt=".2f")
        field_values[f"wc{i}_casing_at_test"] = use(row.casing_at_test, fmt=".2f")
        field_values[f"wc{i}_tds"] = use(row.tds, fmt=".2f")

    casing_types = {
        "S": "Surface",
        "P": "Production",
        "I": "Intermediate",
    }

    pz_types = {
        "R": "Riser",
        "S": "Screen",
        "SC": "Slotted casing",
        "OH": "Open hole",
        "WS": "Wirewound screen",
        "SMP": "Sump",
        "SB": "Screen blank",
        "PC": "Perforated casing",
        "PLV": "Production level",
        "UKN": "Unknown",
    }

    for i, (idx, row) in enumerate(case.iterrows()):
        field_values[f"cs{i}_type"] = (
            casing_types[row.casing_type] if row.casing_type else ""
        )
        field_values[f"cs{i}_from"] = use(row.depth_from, fmt=".2f", accept_zero=True)
        field_values[f"cs{i}_to"] = use(row.depth_to, fmt=".2f")
        field_values[f"cs{i}_diam"] = use(row.case_diam, fmt=".0f")
        field_values[f"cs{i}_material"] = use(row.material)
        field_values[f"cs{i}_cement_from"] = use(row.cement_from, fmt=".2f")
        field_values[f"cs{i}_cement_to"] = use(row.cement_to, fmt=".2f")
        field_values[f"cs{i}_cement_method"] = use(row.cementing_method)
        field_values[f"cs{i}_comments"] = use(
            row.comments,
        )

    field_values["pz_checkbox_open_hole"] = "/Off"
    field_values["pz_checkbox_slotted_casing"] = "/Off"
    field_values["pz_checkbox_screen"] = "/Off"
    if "OH" in pz.pzone_type.unique():
        field_values["pz_checkbox_open_hole"] = "/On"
    if "SC" in pz.pzone_type.unique():
        field_values["pz_checkbox_slotted_casing"] = "/On"
    if "S" in pz.pzone_type.unique() or "WS" in pz.pzone_type.unique():
        field_values["pz_checkbox_screen"] = "/On"

    for i, (idx, row) in enumerate(
        pz[pz.pzone_type.isin(["R", "SC", "S", "WS", "OH", "SMP"])]
        .sort_values(["pzone_from"])
        .iterrows()
    ):
        field_values[f"pz{i}_type"] = pz_types.get(row.pzone_type, "")
        field_values[f"pz{i}_from"] = use(row.pzone_from, fmt=".2f")
        field_values[f"pz{i}_to"] = use(row.pzone_to, fmt=".2f")
        field_values[f"pz{i}_aperture"] = use(row.aperture, fmt=".1f")
        field_values[f"pz{i}_outer_diam"] = use(row.pzone_diam, fmt=".1f")
        field_values[f"pz{i}_material"] = use(row.pzone_material)
        field_values[f"pz{i}_trade_name"] = use(row.trade_name)
        field_values[f"pz{i}_completion_of_base"] = use(row.base_completion)

    for i, (idx, row) in enumerate(dlog.iterrows()):
        field_values[f"log{i}_from"] = use(row.depth_from, fmt=".0f")
        field_values[f"log{i}_to"] = use(row.depth_to, fmt=".0f")
        field_values[f"log{i}_desc"] = use(row.lith_desc)

    for i, (idx, row) in enumerate(devl.iterrows()):
        field_values[f"dev{i}_method"] = ": ".join(
            [x for x in [use(row.method), use(row.comments)] if x]
        )
        field_values[f"dev{i}_hrs"] = use(row.duration, fmt=".1f")

    for i, (idx, row) in enumerate(gsp.iterrows()):
        field_values[f"gp{i}_method"] = use(row.placement_method)
        field_values[f"gp{i}_mesh_size"] = use(row.gravel_sand_size)
        field_values[f"gp{i}_depth_from"] = use(row.depth_from, fmt=".2f")
        field_values[f"gp{i}_depth_to"] = use(row.depth_to, fmt=".2f")

    for i, (idx, row) in enumerate(seal.iterrows()):
        field_values[f"ls{i}_material"] = use(row.seal_material)
        field_values[f"ls{i}_diam"] = use(row.seal_diam, fmt=".1f")
        field_values[f"ls{i}_depth"] = use(row.seal_depth, fmt=".2f")

    writer.update_page_form_field_values(
        writer.pages[0],
        field_values,
        auto_regenerate=False,
    )

    writer.write(file_obj)


def replace_unit_code_as_hyperlink(unit_code):
    if "(" in unit_code:
        endpoint = "aquifer_unit"
        query_param = "aquifer_code"
    else:
        endpoint = "strat_units"
        query_param = "map_symbol"
    if "%" in unit_code and not endpoint.endswith("s"):
        endpoint += "s"
    return (
        f"<a href='/app/{endpoint}?{query_param}={unit_code}&env=prod'>{unit_code}</a>"
    )


def generate_aquifer_code_index(reports=None, add_hyperlinks=False, sagd_conn=None):
    if sagd_conn is None:
        sagd_conn = connect_to_sageodata
    if reports is None:
        reports = pd.read_excel(
            r"r:\dfw_cbd\projects\projects_gw\state\groundwater_toolbox\aquifer_database\reports_index.xlsx"
        )
        reports = reports.dropna(subset=["filename"])

    reportsx = reports.copy()
    ALL_AQUIFERS = sagd_conn.all_aquifer_units()
    ALL_STRAT = sagd_conn.all_strat_units()
    unit_codes = []
    report_lookups = []
    aquifer_codes = list(ALL_AQUIFERS.aquifer_code.unique())
    map_symbols = list(ALL_STRAT[~pd.isnull(ALL_STRAT.map_symbol)].map_symbol.unique())
    all_codes = list(set(aquifer_codes + map_symbols))
    for idx, row in reportsx.iterrows():
        row_units = [u.strip() for u in str(row.aquifers_strat_units).split(",")]
        matched_aquifer_codes = []
        matched_map_symbols = []
        for row_unit in row_units:
            if "%" in row_unit:
                row_unit_re = re.compile(row_unit.replace("%", ".*"))
                matched_aquifer_codes += [
                    c for c in aquifer_codes if row_unit_re.match(c)
                ]
                matched_map_symbols += [c for c in map_symbols if row_unit_re.match(c)]
            else:
                if row_unit in aquifer_codes:
                    matched_aquifer_codes.append(row_unit)
                if row_unit in map_symbols:
                    matched_map_symbols.append(row_unit)
        for matched_aquifer_code in matched_aquifer_codes:
            report_lookups.append(
                {
                    "code": matched_aquifer_code,
                    "code_type": "aquifer_code",
                    "report_filename": row.filename,
                }
            )
        for matched_map_symbol in matched_map_symbols:
            report_lookups.append(
                {
                    "code": matched_map_symbol,
                    "code_type": "map_symbol",
                    "report_filename": row.filename,
                }
            )
        if add_hyperlinks:
            comment = row.comments
            for u in all_codes + row_units:
                if u in comment:
                    comment = re.sub(
                        f"([^a-zA-Z]|^)({u})([^%&a-zA-Z]|$)",
                        f"\\1{replace_unit_code_as_hyperlink(u)}\\3",
                        comment,
                    )
            reportsx.loc[idx, "comments"] = comment.replace("\n", "<br />")
            reportsx.loc[idx, "aquifers_strat_units"] = ", ".join(
                [replace_unit_code_as_hyperlink(u) for u in row_units]
            )
    return pd.DataFrame(report_lookups), reportsx
