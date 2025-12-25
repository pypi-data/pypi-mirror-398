import collections
import io
import re
import os
from pathlib import Path

import sqlalchemy.types
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import wkt


WILMA_DATA_FOLDER = Path(
    r"r:\dfw_cbd\projects\Projects_GW\State\Resource and Condition Monitoring\python-wilma-data"
)

SQLITE_DATABASE = WILMA_DATA_FOLDER / "wilma_data.sqlite3"


WILMAReportingData = collections.namedtuple(
    "WILMAReportingData", ("alloc", "usage", "parcels")
)


def parse_wilma_csv_export(file, **kwargs):
    """Open a WILMA export CSV file.

    Args:
        file (str): filename

    Each file is broken into blocks based on empty lines.

    Returns:
        ``list``: A list of lists. Each inner list contains a string for each line of the
        file.

    """
    if os.path.isfile(str(file)):
        with open(file, "r") as f:
            return parse_wilma_csv_export(f, **kwargs)
    contents = [block.splitlines() for block in file.read().split("\n\n")]
    return contents


def read_allocation_csv(*args, **kwargs):
    """Read and parse a WILMA allocation CSV file.

    Args:
        file (str): filename

    Returns:
        ``pandas.DataFrame``: A dataframe. This function identifies the Levy Year
        from the header block and inserts
        it as the column "levy_year". It also renames "seq_no" to "licence_no",
        "parea" to "pres_area", and adds a column "Alloc_clean" with guaranteed
        numeric values for "Alloc_Qty".

    """
    contents = parse_wilma_csv_export(*args, **kwargs)
    year = None
    with io.StringIO() as buff:
        buff.write("\n".join(contents[2]))
        buff.seek(0)
        df = pd.read_csv(buff, delimiter=",")
    for line in contents[1]:
        if "Levy Year" in line:
            year = int(re.search(r"\d\d\d\d", line).group())
    if not df is None and year:
        df["levy_year"] = year
    df["Alloc_clean"] = pd.to_numeric(
        df.Alloc_Qty.apply(
            lambda v: str(v).strip("(").strip(")").replace(",", "").replace("nan", "")
        )
    )
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(
        columns={
            "seq_no": "licence_seq",
            "parea": "pres_area",
        }
    )
    return df


def sourcedesc_to_unit_hyphen(value):
    """Convert the SOURCEDESC column to a hyphenated unit number wherever
    possible.

    Args:
        value (str): a unit number in any of the WILMA formats.

    Returns:
        ``str``: "6627-123" etc format.

    """
    # The order matters.
    unit_patterns = [
        r"(\d{4}) ?- ?(0\d{5})",
        r"(\d{4}) ?- ?(\d{1,5})",
        r"(\d{4}) ?- ?(\d{5})",
        r"(\d{4})\d{3}WW(\d{5})",
        r"(\d{4})(\d{5})",
    ]
    patterns = [re.compile(p) for p in unit_patterns]
    to_unit_hyphen = lambda m: f"{m.group(1)}-{int(m.group(2))}"
    for pattern in patterns:
        m = pattern.match(value)
        if m:
            return to_unit_hyphen(m)
    return ""


def read_usage_csv(*args, **kwargs):
    """Read and parse a WILMA usage CSV file.

    Args:
        file (str): filename

    Returns:
        ``pandas.DataFrame``: A dataframe. This function identifies the
        Levy Year from the header block and inserts
        it as the column "levy_year". It also renames the following:

        - "resourcetype" to "resource_type"
        - "docno" to "licence_no"
        - "docseq" to "licence_seq"
        - "area" to "pres_area"
        - "sourceid" to "source_id"
        - "resourcegroup" to "resource_group"
        - "meterid" to "meter_id"

        And it adds a value in "source_unit_hyphen" from "source_desc" wherever
        possible.

    """
    contents = parse_wilma_csv_export(*args, **kwargs)
    year = None
    df = None
    for block in contents:
        if len(block) > 0:
            if block[0].startswith("DOCNO,DOCSEQ,wateraccnt,sua"):
                with io.StringIO() as buffer:
                    for line in block:
                        buffer.write(line + "\n")
                    buffer.seek(0)
                    df = pd.read_csv(buffer, delimiter=",")
            else:
                for line in block:
                    if "Levy Year" in line:
                        year = int(re.search(r"\d\d\d\d", line).group())
    if not df is None and year:
        df["levy_year"] = year
    for root in ["METERED", "SUPPLIED1", "ADJUSTMENT", "deemed", "EFFECTIVE"]:
        if root in df.columns:
            df[root] = pd.to_numeric(
                df[root].apply(
                    lambda v: str(v)
                    .strip("(")
                    .strip(")")
                    .replace(",", "")
                    .replace("nan", "")
                )
            )
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(
        columns={
            "resourcetype": "resource_type",
            "docno": "licence_no",
            "docseq": "licence_seq",
            "area": "pres_area",
            "sourceid": "source_id",
            "source_desc": "source_desc",
            "resourcegroup": "resource_group",
            "meterid": "meter_id",
        }
    )
    df["source_unit_hyphen"] = df.sourcedesc.apply(sourcedesc_to_unit_hyphen)
    return df


def read_timestamped_allocation_csv(filename):
    """Read a WILMA allocation CSV file and add filename and timestamp metadata
    in columns of those names.

    Args:
        file (str): filename

    Returns:
        ``pandas.DataFrame``: A dataframe. This function identifies the Levy Year
        from the header block and inserts
        it as the column "levy_year". It also renames "seq_no" to "licence_no",
        "parea" to "pres_area", and adds a column "Alloc_clean" with guaranteed
        numeric values for "Alloc_Qty".

    """
    filename = Path(filename)
    dt = pd.Timestamp(filename.parent.stem)
    df = read_allocation_csv(filename)
    df["downloaded"] = dt
    df["filename"] = str(filename)
    return df


def read_timestamped_usage_csv(filename):
    """Read a WILMA usage CSV file and add filename and timestamp metadata
    in columns of those names.

    Args:
        file (str): filename

    Returns:
        ``pandas.DataFrame``: A dataframe. This function identifies
        the Levy Year from the header block and inserts
        it as the column "levy_year". It also renames the following:

        - "resourcetype" to "resource_type"
        - "docno" to "licence_no"
        - "docseq" to "licence_seq"
        - "area" to "pres_area"
        - "sourceid" to "source_id"
        - "resourcegroup" to "resource_group"
        - "meterid" to "meter_id"

        And it adds a value in "source_unit_hyphen" from "source_desc" wherever
        possible.

    """
    filename = Path(filename)
    dt = pd.Timestamp(filename.parent.stem)
    df = read_usage_csv(filename)
    df["downloaded"] = dt
    df["filename"] = str(filename)
    return df


def read_wilma_licence_parcel_shapefile(filename):
    """Read a shapefile extract from WATER.WILMALicenceParcels.

     Args:
        file (str): filename

    Returns:
        ``pandas.DataFrame``: A dataframe. Renames:

        - "parcel_sub" to "parcel_subtype"
        - "floor_leve" to "floor_level"
        - "accuracy_c" to "accuracy_code"
        - "property_l" to "property_location"
        - "street_nam" to "street_name"
        - "street_typ" to "street_type"
        - "title_owne" to "title_owner_name"
        - "owner_addr" to "owner_address"
        - "prescribed" to "prescribedarea"
        - "management" to "managementarea"
        - "accountnam" to "accountname"

        It also adds NA values to the column "levy_year" as that is current.

    """
    gdf = gpd.read_file(filename, driver="ESRI Shapefile")
    gdf.columns = [c.lower() for c in gdf.columns]
    gdf = gdf.rename(
        columns={
            "parcel_sub": "parcel_subtype",
            "floor_leve": "floor_level",
            "accuracy_c": "accuracy_code",
            "property_l": "property_location",
            "street_nam": "street_name",
            "street_typ": "street_type",
            "title_owne": "title_owner_name",
            "owner_addr": "owner_address",
            "prescribed": "prescribedarea",
            "management": "managementarea",
            "accountnam": "accountname",
        }
    )
    gdf["levy_year"] = pd.NA
    return gdf


def read_timestamped_wilma_licence_parcel_shapefile(filename):
    """Read a shapefile extract from WATER.WILMALicenceParcels and adds
    filename and timestamp metadata in columns of those names.

     Args:
        file (str): filename

    Returns:
        ``pandas.DataFrame``: A dataframe with the following columns renamed:

        - "parcel_sub" to "parcel_subtype"
        - "floor_leve" to "floor_level"
        - "accuracy_c" to "accuracy_code"
        - "property_l" to "property_location"
        - "street_nam" to "street_name"
        - "street_typ" to "street_type"
        - "title_owne" to "title_owner_name"
        - "owner_addr" to "owner_address"
        - "prescribed" to "prescribedarea"
        - "management" to "managementarea"
        - "accountnam" to "accountname"

        It also adds NA values to the column "levy_year" as that is current.

    """
    gdf = read_wilma_licence_parcel_shapefile(filename)
    dt = pd.Timestamp(filename.parent.stem)
    gdf["downloaded"] = dt
    gdf["filename"] = str(filename)
    return gdf


def iter_wilma_downloads():
    """Iterate through download folders.

    Yields a tuple of pathlib.Path, pd.Timestamp objects. The timestamp
    is the day of download. The path is the folder.

    """

    contents = WILMA_DATA_FOLDER.glob("*")
    for path in contents:
        if path.is_dir():
            if re.match(r"\d\d\d\d-\d\d-\d\d", path.stem):
                dl_dt = pd.Timestamp(path.stem)
                yield path, dl_dt


def read_all_wilma_data():
    """Read all data from downloads folder.

    Args:
        folder (str): downloads folder. Optional.

    Returns:
        ``dict``: A dictionary with dataframes under keys "alloc", "usage" and
        "wilma_parcels". See these functions for details of what is in those
        dataframes:

        - :func:`dew_gwdata._wilma.read_timestamped_allocation_csv`
        - :func:`dew_gwdata._wilma.read_timestamped_usage_csv`
        - :func:`dew_gwdata._wilma.read_timestamped_wilma_licence_parcel_shapefile`

    """

    READ_MAP = {
        "alloc": (
            "Licence Allocation (Previous Years)",
            "Licence Allocation- Previous Years *.csv",
            read_timestamped_allocation_csv,
        ),
        "usage": (
            "Usage (Bundled)",
            "Usage - Bundled *.csv",
            read_timestamped_usage_csv,
        ),
        "wilma_parcels": (
            "ENVGIS WILMA Parcels",
            "water_wilma_licence_parcels.shp",
            read_timestamped_wilma_licence_parcel_shapefile,
        ),
    }

    data = {k: [] for k in READ_MAP.keys()}
    for path, timestamp in iter_wilma_downloads():
        for file_type_code, (file_type, glob_pattern, read_func) in READ_MAP.items():
            for fn in path.glob(glob_pattern):
                print(fn)
                df = read_func(fn)
                data[file_type_code].append(df)
    return data


def read_all_wilma_data_to_flat():
    """Read all data from downloads folder.

    Args:
        folder (str): downloads folder. Optional.

    Returns:
        ``collections.namedtuple``: A named tuple of three dataframes: ``alloc, usage, parcels``.
        See these functions for details of what is in those
        dataframes:

        - :func:`dew_gwdata._wilma.read_timestamped_allocation_csv`
        - :func:`dew_gwdata._wilma.read_timestamped_usage_csv`
        - :func:`dew_gwdata._wilma.read_timestamped_wilma_licence_parcel_shapefile`

    """
    data = read_all_wilma_data()

    data_flat = {}
    for file_type_code, dfs in data.items():
        df = pd.concat(dfs)
        df["levy_year"] = df["levy_year"].fillna("NA")
        df = (
            df.groupby("levy_year")
            .apply(filter_to_keep_latest_download)
            .reset_index(drop=True)
        )
        data_flat[file_type_code] = df

    alloc = data_flat["alloc"]
    usage = data_flat["usage"]
    wilma_parcels = data_flat["wilma_parcels"]
    wilma_data = WILMAReportingData(alloc=alloc, usage=usage, parcels=wilma_parcels)
    return wilma_data


def filter_to_keep_latest_download(df):
    """Remove all but the most recently downloaded dataframe subset."""
    max_download = df["downloaded"].max()
    return df[df["downloaded"] == max_download]


def identify_dtypes(df):
    """Identify dataframe datatypes for export to sqlite3.

    Args:
        df (pandas.DataFrame): dataframe

    Returns:
        ``dict``: A dictionary mapping column name (str) to sqlalchemy.types - only Integer,
        Float, DateTime, and String are catered for.

    """
    dtypes = {}
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        if dtype_str.startswith("int"):
            dtypes[col] = sqlalchemy.types.Integer()
        elif dtype_str.startswith("float"):
            dtypes[col] = sqlalchemy.types.Float()
        elif dtype_str.startswith("datetime"):
            dtypes[col] = sqlalchemy.types.DateTime()
        else:
            dtypes[col] = sqlalchemy.types.String()
    return dtypes


def update_db(alloc, usage, wilma_parcels, db_fn=None):
    """Update a sqlite3 database with the flat dataframes from
    :func:`dew_gwdata._wilma.read_all_data_flat`.

    Args:
        db_fn (str): database filename

    """
    if db_fn is None:
        db_fn = SQLITE_DATABASE

    con = sqlalchemy.create_engine("sqlite:///" + str(Path(db_fn).resolve()))
    print(f"Opened WILMA connection to : {con}")

    alloc.to_sql("alloc", con, if_exists="replace", dtype=identify_dtypes(alloc))
    usage.to_sql("usage", con, if_exists="replace", dtype=identify_dtypes(usage))
    wilma_parcels["geometry"] = wilma_parcels["geometry"].astype(str)
    wilma_parcels.to_sql(
        "wilma_parcels", con, if_exists="replace", dtype=identify_dtypes(wilma_parcels)
    )


def connect_to_wilma_sqlite_db(db_fn=None):
    """Connect to sqlite3 database created with :func:`update_db`.

    Args:
        db_fn (str): database filename

    Returns:
        ``sqlalchemy.Engine``

    """
    if db_fn is None:
        db_fn = SQLITE_DATABASE

    con = sqlalchemy.create_engine("sqlite:///" + str(Path(db_fn).resolve()))
    return con.connect()


def read_from_wilma_sqlite_db(db_fn=None):
    """Read dataframes from WILMA sqlite3 database.

    Args:
        db_fn (str): database filename

    Returns:
        ``collections.namedtuple``: A named tuple of three dataframes: ``alloc, usage, parcels``.
        These contain all data from the WILMA exports. The columns in ``alloc`` are:

        - x

        The columns in ``usage`` are:

        - index (int)
        - licence_no (int)
        - licence_seq (int)
        - wateraccnt
        - sua
        - source_id (int)
        - sourcedesc (str): unit number in hyphenated WILMA format e.g. 6527-01234. It may be erroneous
          and some fields contain random text descriptions, not unit numbers.
        - meter_id
        - easting (int): from WILMA, not SA Geodata
        - northing  (int): from WILMA, not SA Geodata
        - resource_type (str): e.g. 'Underground'
        - resource_group (str): the licensing source breakdown e.g. "EMLR Angas Bremer Limestone GWMZ"
        - pres_area (str): the PWA/PWRA
        - year (int): the levy year so for example 2014 means 2013-14 financial year.
        - metered (int): volume in kL
        - supplied1 (int): volume in kL
        - adjustment (int): volume in kL
        - deemed (int): volume in kL
        - effective (int): volume in kL - this is the one to use, it's supposed to represent actual
          water taken
        - levy_year (int): the levy year so for example 2014 means 2013-14 financial year.
        - source_unit_hyphen (str): the unit number in proper hyphenated format, if it can be identified
          in SA Geodata. The values here are guaranteed to refer to actual wells in SAGD.
        - downloaded (timestamp): date of download from WILMA Reporting
        - filename (str): source of the data on the network drive.
        - unit_hyphen (str): same as source_unit_hyphen column
        - latitude (float):
        - longitude (float):

        The columns in ``wilma_parcels`` are:

        - xx

    See these functions for further details of what is in the returned dataframes.

    - :func:`dew_gwdata._wilma.read_timestamped_allocation_csv`
    - :func:`dew_gwdata._wilma.read_timestamped_usage_csv`
    - :func:`dew_gwdata._wilma.read_timestamped_wilma_licence_parcel_shapefile`

    """
    con = connect_to_wilma_sqlite_db(db_fn=db_fn)

    alloc = pd.read_sql("select * from alloc", con)
    usage = pd.read_sql("select * from usage", con)
    wilma_parcels = pd.read_sql("select * from wilma_parcels", con)
    wilma_parcels = gpd.GeoDataFrame(
        wilma_parcels, geometry=wilma_parcels.geometry.apply(wkt.loads)
    )
    wilma_data = WILMAReportingData(alloc=alloc, usage=usage, parcels=wilma_parcels)
    return wilma_data


def query_alloc_for_licence_no(con, licence_no):
    """Query and return subset of allocation data for a licence number.

    Args:
        licence_no (int): licence number.

    Returns:
        ``pandas.DataFrame``

    """
    return pd.read_sql(
        f"select * from alloc where resource_type = 'Underground' and licence_no = {licence_no:.0f}",
        con,
    )


def query_usage_for_unit_hyphen(con, unit_hyphen):
    """Query and return subset of usage data for a hyphenated unit number.

    Args:
        unit_hyphen (str): unit number e.g. "7022-1234"

    Returns:
        ``pandas.DataFrame``

    """
    return pd.read_sql(
        f"select * from usage where resource_type = 'Underground' and source_unit_hyphen = '{unit_hyphen}'",
        con,
    )


def query_usage_for_licence_no(con, licence_no):
    """Query and return subset of usage data for a licence number.

    Args:
        licence_no (int): licence number.

    Returns:
        ``pandas.DataFrame``

    """
    return pd.read_sql(
        f"select * from usage where resource_type = 'Underground' and licence_no = {licence_no:.0f}",
        con,
    )


def total_taking(allocs):
    """For a set of licence allocations, return the total Taking
    allocations as a Series. The index is the levy_year, the values
    are the total allocations as kL.

    """
    return (
        allocs[lambda x: (x.alloc_type == "Taking") & (x.uom == "kL")]
        .groupby("levy_year")
        .alloc_clean.sum()
    )


# licence_no = 5001
# licence_no = 5389
# licence_no = 12335
# licence_no = 12333
# licence_no = 12877
# licence_no = 12284
# licence_no = 141372


def summarise_usage_table(usage_df):
    """Given usage table, summarise the history take from all GW sources for
    that licence.

    Args:
        usage_df (pd.DataFrame): must have columns "levy_year", "sourcedesc",
            "effective"

    Returns:
        ``pandas.DataFrame``: A dataframe with index column "levy_year" - remaining columns are
        the values in "sourcedesc" and an additional one "total".

    All units in output are ML. Input units in "effective" must be kL.

    """
    usage_series_by_source = usage_df.groupby(
        ["levy_year", "sourcedesc"]
    ).effective.sum()
    udf = (usage_series_by_source.unstack(level=1) / 1e3).round(3)
    sum_udf = udf.sum(axis=1)
    udf = pd.concat([udf, sum_udf.to_frame()], axis=1).rename(columns={0: "total"})
    return udf


def summarise_taking_alloc_history(alloc_df):
    """Given allocation table, summarise the history of GW take allocations.

    Args:
        alloc_df (pd.DataFrame): must have columns "levy_year", "licence_no",
            "licence_seq", "alloc_purpose", "uom", and "alloc_clean"

    Returns:
        ``pandas.DataFrame``: A dataframe with index columns "levy_year", "licence_no", "licence_seq",
        and remaining columns are the values in "alloc_purpose" and an additional
        one "total".

    All units in output are ML. Input units in alloc_clean must be kL.

    Note: Allocations in units other than kL are removed.

    """
    colsa = ["levy_year", "licence_no", "licence_seq", "alloc_purpose", "alloc_clean"]
    adf = alloc_df[lambda x: x.uom == "kL"][colsa]
    adf = adf.set_index(["levy_year", "licence_no", "licence_seq", "alloc_purpose"])
    adf = (adf.unstack(level=3).fillna(pd.NA) / 1e3).round(3)
    adf_sum = adf.sum(axis=1).to_frame(name="total")
    adf.columns = [c[1] for c in adf.columns]
    adf = pd.concat([adf, adf_sum], axis=1)
    return adf


def plot_alloc_usage_for_licenced_well(
    unit_hyphen, con=None, figsize=(9, 5), allocs=None, usage=None, return_all=False
):
    import matplotlib.pyplot as plt

    usage_ = query_usage_for_unit_hyphen(con, unit_hyphen)
    usage_subset = usage_[usage_.source_unit_hyphen == unit_hyphen]
    licence_nos = usage_subset.licence_no.unique()
    results = []
    for licence_no in licence_nos:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        result = plot_alloc_usage_for_licence(
            licence_no,
            con=con,
            highlight_source=unit_hyphen,
            ax=ax,
            allocs=allocs,
            usage=usage,
            return_all=return_all,
        )
        results.append(result)
    return results


def plot_alloc_usage_for_licence(
    licence_no,
    con=None,
    allocs=None,
    usage=None,
    ax=None,
    return_all=False,
    highlight_source=None,
):
    from matplotlib import ticker as mticker
    import matplotlib.pyplot as plt

    if allocs is None:
        alloc_ = query_alloc_for_licence_no(con, licence_no)
    else:
        alloc_ = allocs
    if usage is None:
        usage_ = query_usage_for_licence_no(con, licence_no)
    else:
        usage_ = usage

    if ax is None:
        fig = plt.figure(figsize=(9, 5))
        ax = fig.add_subplot(111)

    alloc_series = total_taking(
        alloc_[
            (alloc_.licence_no == licence_no) & (alloc_.resource_type == "Underground")
        ]
    )
    usage_series = (
        usage_[
            (usage_.licence_no == licence_no) & (usage_.resource_type == "Underground")
        ]
        .groupby("levy_year")
        .effective.sum()
    )
    usage_series_by_source = (
        usage_[
            (usage_.licence_no == licence_no) & (usage_.resource_type == "Underground")
        ]
        .groupby(["levy_year", "sourcedesc"])
        .effective.sum()
    )
    usage_by_source = usage_series_by_source.unstack(level=1).fillna(0)
    keep_cols = []
    for col in usage_by_source.columns:
        if (usage_by_source[col] != 0).any():
            keep_cols.append(col)
    usage_by_source = usage_by_source[keep_cols]
    if len(usage_by_source.columns) < 2:
        highlight_source = None

    ax.plot(
        alloc_series.index,
        alloc_series * 1e3,
        color="tab:brown",
        label="Taking allocation(s)",
        drawstyle="steps-mid",
    )
    usage_width = 0.8

    bar_cumulative = np.zeros_like(usage_by_source.index.values).astype(float)
    for sourcedesc in usage_by_source.columns:
        usage_source = usage_by_source[sourcedesc]
        bar_data = usage_source * 1e3
        lw = 0
        ec = "none"
        if (
            sourcedesc == highlight_source
            or usage_.loc[usage_.sourcedesc == sourcedesc, "source_unit_hyphen"].iloc[0]
            == highlight_source
        ):
            lw = 2
            ec = "red"
        ax.bar(
            usage_source.index,
            bar_data,
            bottom=bar_cumulative,
            width=usage_width,
            linewidth=lw,
            edgecolor=ec,
            label=f"Metered usage ({sourcedesc})",
        )
        if len(usage_by_source.columns) > 1:
            for i, (levy_year, value_kl) in enumerate(usage_source.items()):
                source_frac = value_kl / usage_series.loc[levy_year]
                if source_frac >= 0.2:
                    value_ml = value_kl / 1e3
                    value_plot = bar_cumulative[i] + (value_kl * 1e3) / 2
                    ax.text(
                        levy_year,
                        value_plot,
                        f"{value_ml:.0f} ML",
                        ha="center",
                        va="center",
                        fontsize="x-small",
                        color="white",
                    )
        bar_cumulative += bar_data.values.astype(float)

    for levy_year, value_kl in usage_series.items():
        value_ml = value_kl / 1e3
        y0, y1 = ax.get_ylim()
        yd = (y1 - y0) / 40
        ax.text(
            levy_year,
            (value_kl * 1e3) + yd,
            f"{value_ml:.0f} ML",
            ha="center",
            va="bottom",
            fontsize="x-small",
            fontweight="normal",
            bbox=dict(facecolor="white", alpha=0.5, edgecolor="grey"),
        )

    ax.set_ylabel("Volume", fontsize="small")
    ax.set_xlabel("Levy year", fontsize="small")
    ax.legend(frameon=True, fontsize="small", ncol=2)
    ax.set_title(
        f"Underground take allocations and usage: licence {licence_no}",
        fontsize="small",
    )
    ax.grid(ls=":", lw=0.5, color="grey")
    y0, y1 = ax.get_ylim()
    yd = y1 - y0
    new_y1 = y1 + (yd / 6)
    ax.set_ylim(y0, new_y1)
    x0 = min([alloc_series.index.min(), usage_series.index.min()])
    x1 = max([alloc_series.index.max(), usage_series.index.max()])
    ax.set_xticks(np.arange(x0, x1 + 1, 1))
    _ = plt.setp(ax.get_xticklabels(), fontsize="small", rotation=90)
    _ = plt.setp(ax.get_yticklabels(), fontsize="small")
    ax.yaxis.set_major_formatter(mticker.EngFormatter("L"))

    if return_all:
        return {
            "licence_no": licence_no,
            "ax": ax,
            "alloc": alloc_,
            "usage": usage_,
            "alloc_series": alloc_series,
            "usage_series": usage_series,
            "usage_series_by_source": usage_series_by_source,
            "usage_by_source": usage_by_source,
        }
    else:
        return ax


def plot_usage_for_licenced_well(
    unit_hyphen,
    con=None,
    usage=None,
    ax=None,
    return_all=False,
):
    from matplotlib import ticker as mticker
    import matplotlib.pyplot as plt

    if usage is None:
        usage_ = query_usage_for_unit_hyphen(con, unit_hyphen)
    else:
        usage_ = usage

    if ax is None:
        fig = plt.figure(figsize=(8, 4))
        ax = fig.add_subplot(111)

    usage_subset = usage_[usage_.source_unit_hyphen == unit_hyphen]
    usage_series = (
        usage_subset[usage_subset.resource_type == "Underground"]
        .groupby("levy_year")
        .effective.sum()
        * 1e3
    )

    usage_width = 0.5
    lw = 0
    ec = "none"
    ax.bar(
        usage_series.index,
        usage_series.values,
        width=usage_width,
        linewidth=lw,
        edgecolor=ec,
        label=unit_hyphen,
    )

    if max(usage_series) < 10e6:
        convert_val = lambda v: (v, f"{v:.0f} kL")
    else:
        convert_val = lambda v: (v, f"{v / 1e3:.0f} ML")

    for levy_year, value_l in usage_series.items():
        value_kl = value_l / 1e3
        v, text_label = convert_val(value_kl)
        value_ml = value_kl / 1e3
        y0, y1 = ax.get_ylim()
        yd = y1 - y0
        ax.text(
            levy_year,
            (value_l) + yd / 40,
            text_label,
            ha="center",
            va="bottom",
            fontsize="x-small",
            fontweight="normal",
            bbox=dict(facecolor="white", alpha=0.5, edgecolor="grey"),
        )

    ax.set_ylabel("Volume", fontsize="small")
    ax.set_xlabel("Levy year", fontsize="small")
    ax.legend(frameon=True, fontsize="small", ncol=2)
    ax.set_title(
        f"Metered underground effective usage: {unit_hyphen}",
        fontsize="small",
    )
    ax.grid(ls=":", lw=0.5, color="grey")
    y0, y1 = ax.get_ylim()
    yd = y1 - y0
    new_y1 = y1 + (yd / 6)
    ax.set_ylim(y0, new_y1)
    x0 = min([usage_series.index.min(), usage_series.index.min()])
    x1 = max([usage_series.index.max(), usage_series.index.max()])
    ax.set_xticks(np.arange(x0, x1 + 1, 1))
    _ = plt.setp(ax.get_xticklabels(), fontsize="small", rotation=90)
    _ = plt.setp(ax.get_yticklabels(), fontsize="small")
    ax.yaxis.set_major_formatter(mticker.EngFormatter("L"))

    if return_all:
        return {
            "unit_hyphen": unit_hyphen,
            "ax": ax,
            "usage": usage_,
            "usage_series": usage_series,
        }
    else:
        return ax
