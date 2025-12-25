from collections import ChainMap
import logging

import requests
import pandas as pd

try:
    from pandas import json_normalize
except:
    from pandas.io.json import json_normalize
import sa_gwdata

from .utils import *

logger = logging.getLogger(__name__)


def fetch_hydstra_dtw_data(
    wells,
    interval="day",
    multiplier=5,
    agg_func="mean",
    exclude_hydstra_qcs=("Missing", "undefined"),
):
    """Fetch WL data from Hydstra.

    Args:
        wells: either a list of :class:`sa_gwdata.Well` objects
            or a :class:`pandas.DataFrame` with a column
            "unit_long"
        interval (str): aggregate to an interval of *multiplier*
            times 1 of a "year", "month", "day", "hour", "minute",
            "second"
        multiplier (int): see above
        agg_func (str): either "mean", "min", "max"
        exclude_hydstra_qcs (sequence of str): Hydstra quality codes to remove
            from the final DataFrame.

    Returns:
        :class:`pandas.DataFrame` with columns "well_id", "obs_date",
        "dtw", and "quality_code"

    Data will be retrieved from the hydllpx-server application currently
    configured to run at http://envtelem04:8096/docs. (This application has in
    turn been configured to access the production Hydstra application on
    envtelem03).

    Only Hydstra variable 114.00 (i.e. depth to water) will currently
    be queried for.

    """
    try:
        assert isinstance(wells[0], sa_gwdata.Well)
        hyd_sites = [f"G{w.unit_long}" for w in wells]
    except (AssertionError, KeyError) as e:
        try:
            hyd_sites = [f"G{x}" for x in wells.unit_long]
        except AttributeError:
            hyd_sites = wells

    quality_codes = {}
    json_data = []

    for chunk_hyd_sites in chunk(hyd_sites, 160):
        try:
            r = requests.get(
                f"http://envtelem04:8096/sites/{','.join(chunk_hyd_sites)}/traces",
                params=dict(
                    varlist="114.00",
                    data_type=agg_func,
                    interval=interval,
                    multiplier=multiplier,
                ),
            )
        except requests.exceptions.ConnectionError:
            r_json = {}
        try:
            r_json = r.json()
        except:
            print("Error parsing JSON")
            break
        if "return" in r_json:
            qc = dict(
                ChainMap(
                    *[
                        {int(k): v for k, v in trace["quality_codes"].items()}
                        for trace in r.json()["return"]["traces"]
                    ]
                )
            )
            quality_codes.update(qc)
            if len(r_json["return"]["traces"]):
                json_data += r_json["return"]["traces"]

    quality_codes[255] = "undefined"
    if len(json_data):
        df = json_normalize(
            json_data, "trace", [["site"], ["site_details", "short_name"]]
        )
        df_col_map = {
            "v": "dtw",
            "t": "obs_date",
            "q": "quality_code",
            "site": "unit_long",
            "site_details.short_name": "well_id",
        }
        df = df[df_col_map.keys()].rename(columns=df_col_map)
        df.loc[:, "dtw"] = df.dtw.astype(float)
        str_cols = ["well_id"]
        df.loc[:, str_cols] = df[str_cols].astype(str)
        df.loc[:, "unit_long"] = df.unit_long.str[1:].astype(int)
        df.loc[:, "quality_code"] = df.quality_code.map(quality_codes)
        df.loc[:, "obs_date"] = pd.to_datetime(df.obs_date, format="%Y%m%d%H%M%S")
    else:
        df = pd.DataFrame(
            [], columns=["well_id", "obs_date", "unit_long", "dtw", "quality_code"]
        )
    return df[~(df.quality_code.isin(exclude_hydstra_qcs))]


def hydstra_quality(df):
    """Return a pandas DataFrame showing the number of
    measurements with various quality codes in a water
    level dataset *df*.

    """
    return df.groupby(["well_id", "quality_code"]).agg(
        {"obs_date": ["count", "min", "max"]}
    )


def resample_logger_wls(
    df, period="W", reduction_func=max, dt_col="obs_date", wl_col="rswl"
):
    """Resample logger WLs.

    Args:
        df (:class:`pandas.DataFrame`): logger WL dataset
        period (str): period to resample to, default "W" for week
        reduction_func (func): function to reduce with, default "max"

    Returns: :class:`pandas.DataFrame` with the columns *dt_col* and *wl_col*.

    """
    return (
        df.resample(period, on=dt_col)[wl_col]
        .apply(reduction_func)
        .to_frame(wl_col)
        .reset_index()
    )
