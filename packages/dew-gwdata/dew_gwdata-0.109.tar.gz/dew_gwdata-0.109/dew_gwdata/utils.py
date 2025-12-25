import io
import datetime
from string import Formatter
from pathlib import Path
import os
import re
import logging

import pandas as pd
import requests
import pyodbc
import sqlparse
import numpy as np
from sa_gwdata import Wells, UnitNumber

WEB_APP_HOST = "neptune"
WEB_APP_PORT = 8191


logger = logging.getLogger(__name__)


def get_pretty_file_size(path):
    """Return a pretty file size with GB/MB/KB/B suffix for a file.

    Args:
        path (str): filename path

    Returns:
        string: e.g. "5.25 MB" with the suffix suitably selected.

    """
    stats = os.stat(str(path))
    kb = stats.st_size / 1024
    mb = kb / 1024
    gb = mb / 1024
    if gb > 1:
        size = f"{gb:.2f} GB"
    elif mb > 1:
        size = f"{mb:.2f} MB"
    elif kb > 1:
        size = f"{kb:.0f} KB"
    else:
        size = f"{kb * 1024:.0f} B"
    return size


def timestamp_acst(*args):
    """Convert a pandas Timestamp to ACST

    Arguments are passed directly to pandas.Timestamp's constructor.

    Returns a pandas Timestamp set to ACST (UTC + 9.5 hours).

    """
    return pd.Timestamp(*args, tzinfo=datetime.timezone(datetime.timedelta(hours=9.5)))


class SQL:
    r"""Represents an SQL query

    Lower-case string template fields are filled directly with the content of the
    keyword argument, while upper-case ones are understood as iterators over a variety
    of sequence types (each then represented in the Oracle SQL correctly according to the
    sequence's element data type). E.g.

        >>> from dew_gwdata import SQL
        >>> query = SQL(
        ...     "select * from dhdb.dd_drillhole_vw where drillhole_no in {dh_no}",
        ...     dh_no=1
        ... )
        >>> for sql in query:
        ...     print(sql)
        SELECT *
        FROM dhdb.dd_drillhole_vw
        WHERE drillhole_no IN 1

    Or for a sequence data type:

    >>> from dew_gwdata import SQL
        >>> sequence_query = SQL(
        ...     "select * from dhdb.dd_drillhole_vw where drillhole_no in {DH_NO}",
        ...     dh_no=[1, 2, 3, 4, 5, 6, 7]
        ... )
        >>> for sql in sequence_query:
        ...     print(sql)
        SELECT *
        FROM dhdb.dd_drillhole_vw
        WHERE drillhole_no IN (1,2,3,4,5,6,7)

    To illustrate how a long list of qualifiers is automatically broken into the
    maximum acceptable by the database engine, let's artifically reduce the
    default of 1000 to something we can easily visualize:

        >>> sequence_query.chunksize = 3
        >>> for i, sql in enumerate(sequence_query):
        ...     print((i, sql))
        (0, 'SELECT *\nFROM dhdb.dd_drillhole_vw\nWHERE drillhole_no IN (1,2,3)')
        (1, 'SELECT *\nFROM dhdb.dd_drillhole_vw\nWHERE drillhole_no IN (4,5,6)')
        (2, 'SELECT *\nFROM dhdb.dd_drillhole_vw\nWHERE drillhole_no IN (7)')

    The kwarg to_str provides a function which turns the elements from field_list
    to a string. By default it is determined by the type of the first element.

    You can re-use a `dew_gwdata.SQL` object with a new field_list:

        >>> sequence_query_2 = SQL(sequence_query, [8, 9, 10])
        >>> for sql in sequence_query_2:
        ...     print(sql)
        SELECT *
        FROM dhdb.dd_drillhole_vw
        WHERE drillhole_no IN (8,9,10)

    """

    def __init__(
        self, sql, *args, to_str=None, chunksize=1000, ignore_fields=None, **kwargs
    ):
        if isinstance(sql, SQL):
            sql = sql.sql

        if ignore_fields is None:
            ignore_fields = ()

        self.chunksize = chunksize
        self.sql = sqlparse.format(sql, reindent=True, keyword_case="upper")

        fields = [
            fname
            for _, fname, _, _ in Formatter().parse(self.sql)
            if fname and (not fname in ignore_fields) and (not re.match(r"\d+", fname))
        ]

        # Assign a field name to each positional argument. Most of the time there
        # will only be one positional argument, and only one field in the SQL query.
        # But in general, we assign them in the order we find them, and clobber
        # anything from **kwargs in the process.

        for i in range(len(args)):
            kwargs[fields[i]] = args[i]

        # Fields in uppercase are to be filled as lists. There must only be one because
        # it's not easy to work out whether they should be joined with or, and, or whatever.
        # Fields in lowercase are to be filled as items for every query.

        uppercase_fields = [x for x in fields if x.upper() == x]
        lowercase_fields = [x for x in fields if not x in uppercase_fields]
        assert len(set(uppercase_fields)) in (0, 1)

        # logger.debug(f"uppercase_fields: {uppercase_fields}")
        # logger.debug(f"lowercase_fields: {lowercase_fields}")

        # If an SQL field e.g. DH_NO is present in kwargs in lowercase, then we need
        # to convert the kwargs to uppercase, so that everything else works sensibly.

        for upper_field in uppercase_fields:
            keys = list(kwargs.keys())
            for k in keys:
                if k == upper_field.lower():
                    kwargs[upper_field] = kwargs[k]
                    del kwargs[k]
                    break

        if len(uppercase_fields) > 0:
            items = kwargs[uppercase_fields[0]]
            if isinstance(items, Wells):
                items = getattr(
                    items, uppercase_fields[0].lower()
                )  # e.g. for {DH_NO}, fetch [w.dh_no for w in Wells]
            elif isinstance(items, pd.DataFrame):
                items = items[uppercase_fields[0].lower()].tolist()
            self.field_list = items
            self.field_list_name = uppercase_fields[0]  # remain uppercase
        else:
            self.field_list = []
            self.field_list_name = None

        # Work out the string formatting.

        self.to_str_funcs = {}
        for field_name, example in kwargs.items():
            if field_name == field_name.upper():
                if isinstance(example, pd.DataFrame):
                    example = example.iloc[0]
                else:
                    logger.debug(
                        f"Attempting to retrieve first item of example={example} ({type(example)})"
                    )
                    try:
                        example = example[0]
                        logger.debug(f"Successful. Example={example} ({type(example)})")
                    except IndexError:
                        example = None
                        logger.debug(
                            f"IndexError - failed. Example remains={example} ({type(example)})"
                        )

            if example is None:
                # Field list is empty. We need a valid SQL query, so that we
                # return an empty table with the correct column names.
                # We assume that nothing will match an empty string in the
                # SQL where clause.

                self.to_str_funcs[field_name] = lambda x: "'{}'".format(str(x))
                self.field_list = [""]

            else:
                if isinstance(example, int) or isinstance(example, np.int64):
                    self.to_str_funcs[field_name] = lambda x: str(int(x))
                elif isinstance(example, float):
                    self.to_str_funcs[field_name] = lambda x: str(float(x))
                elif (
                    isinstance(example, datetime.datetime)
                    or isinstance(example, pd.Timestamp)
                    or isinstance(example, datetime.date)
                ):
                    self.to_str_funcs[field_name] = lambda x: x.strftime(
                        "'%Y-%m-%d %H:%M:%S'"
                    )
                else:
                    self.to_str_funcs[field_name] = lambda x: "'{}'".format(str(x))

        if self.field_list_name:
            del kwargs[self.field_list_name]

        self.scalar_fields = kwargs

    def __iter__(self):
        scalar_inserts = {
            k: self.to_str_funcs[k](v) for k, v in self.scalar_fields.items()
        }

        if len(self.field_list):
            for sub_list in chunk(self.field_list, self.chunksize):
                to_str = self.to_str_funcs[self.field_list_name]
                sub_list_str = "(" + ",".join(map(to_str, sub_list)) + ")"
                inserts = dict(scalar_inserts)
                inserts[self.field_list_name] = sub_list_str
                yield self.sql.format(**inserts)
        elif len(scalar_inserts):
            yield self.sql.format(**scalar_inserts)
        else:
            yield self.sql


def chunk(l, n=1000):
    """Yield successive n-sized chunks from a list l.

    >>> from dew_gwdata.utils import chunk
    >>> for x in chunk([0, 1, 2, 3, 4], n=2):
    ...     print(x)
    [0, 1]
    [2, 3]
    [4]

    """
    y = 0
    for i in range(0, len(l), n):
        y += 1
        yield l[i : i + n]
    if y == 0:
        yield l


def apply_well_id(row, columns=("obs_no", "unit_hyphen", "dh_no")):
    for col in columns:
        if row[col]:
            return row[col]
    return ""


def cleanup_columns(df, keep_cols="well_id", drop=(), remove_metadata=False):
    """Remove unneeded drillhole identifier columns.

    Args:
        df (pandas DataFrame): dataframe to remove columns from
        keep_cols (sequence of str): columns to retain (only applies to the
            well identifiers columns; any other columns will be retained
            regardless)
        drop (sequence of strings): columns to remove
        remove_metadata (bool): remove the "modified_date", "creation_date"
            "modified_by" and "modified_date" columns if True and present.
            False by default.

    Returns:
        pandas.DataFrame

    """
    if not "well_id" in df.columns and [
        c for c in df.columns if c in ("obs_no", "unit_hyphen", "dh_no")
    ]:
        cols = [x for x in df.columns]
        df["well_id"] = df.apply(apply_well_id, axis="columns")
        df = df[["well_id"] + cols]
    if remove_metadata:
        for col in df:
            if (
                "modified_date" in col
                or "creation_date" in col
                or "modified_by" in col
                or "created_by" in col
            ):
                df = df.drop(col, axis=1)
    keep_columns = []
    for col in df.columns:
        if (
            col
            in (
                "well_id",
                "dh_no",
                "unit_long",
                "unit_hyphen",
                "obs_no",
                "dh_name",
                "easting",
                "northing",
                "zone",
                "latitude",
                "longitude",
                "aquifer",
            )
            and not col in keep_cols
        ):
            pass
        else:
            keep_columns.append(col)
    keep_columns = [c for c in keep_columns if not c in drop]
    return df[keep_columns]


def rmdir(directory):
    """Delete a directory and all its contents without confirmation."""
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


def camel_to_underscore(key):
    """Convert a CamelCase string to lowercase underscore-separated.

    Example::

        >>> camel_to_underscore("InputTimeSeriesUniqueIds")
        'input_time_series_unique_ids'

    """
    chars = []
    for char in key:
        if bool(re.match("[A-Z]", char)):
            if len(chars) != 0:
                chars.append("_")
            chars.append(char.lower())
        else:
            chars.append(char)
    return "".join(chars)


def resize_image(image, width=None, height=None):
    """Resize an image while retaining the aspect ratio.

    Args:
        image (PIL.Image)
        width (int)
        height (int)

    Returns:
        PIL.Image

    """
    if width == -1:
        width = None
    if height == -1:
        height = None
    if width and not height:
        return image.resize((width, int(image.height * (width / image.width))))
    elif height and not width:
        return image.resize((int(image.width * (height / image.height)), height))
    elif height and width:
        return image.resize((width, height))
    else:
        return image


def add_well_ids_to_query_result(df, sagd_conn=None):
    """Add well identifiers to query result which only has "dh_no".

    Args:
        df (pandas.DataFrame): table of results, must contain "dh_no" column
        sagd_conn (:class:`sageodata_db.SAGeodataConnection`): optional

    Returns:
        pandas.DataFrame: The table returned will have the columns
        "dh_no", "unit_hyphen", "obs_no", "dh_name" at the start, followed
        by all the original columns from **df**.

    """
    if not sagd_conn:
        from .sageodata_database import connect

        sagd_conn = connect()
    id_cols = ["dh_no", "unit_hyphen", "obs_no", "dh_name"]
    fdf = pd.merge(
        df, sagd_conn.wells_summary(df.dh_no)[id_cols], on="dh_no", how="left"
    )
    cols = [c for c in fdf.columns if not c in id_cols]
    return fdf[id_cols + cols]


class SQLServerDb:
    """Connect to a SQL Server database

    Args:
        conn (option, pyodbc.Connection)
        use_api (bool, default False)
        fallback_to_api (bool, default True)

    By default the SQL Server databases are not accessible to users at DEW.
    If your Windows user does not have at least read-only access, as is likely,
    there is an option to use the web application included as part of ``dew_gwdata``
    by setting ``use_api=True``.

    **Do not instantiate directly.** Instead, create a child class and define the
    class level attribute API_ENDPOINT_NAME, this should be a corresponding
    function in ``dew_gwdata.webapp.handlers.api``. Also create a method
    ``connect`` which takes no arguments in the child class. This method
    should create a database connection in the attribute ``conn``.

    """

    API_ENDPOINT_NAME = None

    def __init__(self, conn=None, use_api=False, fallback_to_api=True):
        self.api_endpoint = (
            f"http://{WEB_APP_HOST}:{WEB_APP_PORT}/api/{self.API_ENDPOINT_NAME}"
        )
        self.use_api = use_api
        if conn is None:
            try:
                self.connect()
            except pyodbc.InterfaceError:
                if not use_api and fallback_to_api:
                    logger.warning(
                        "cannot use db (use_api=False), user probably does not have access. use_api force-set to True"
                    )
                    self.use_api = True
                elif not use_api and not fallback_to_api:
                    raise

    def query(self, sql):
        """Query the database.

        Args:
            sql (str): query to use

        To query direct your windows user will need access to
        Otherwise this code will redirect to use the dew_gwdata
        API which is hopefully running on an account that does
        have access (e.g. syski on bunyip).

        Returns:
            pandas.DataFrame

        """
        logger.debug(f"use_api={self.use_api} - sql={sql}")
        if not self.use_api:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            results = [list(r) for r in cursor.fetchall()]
            field_names = [c[0] for c in cursor.description]
            df = pd.DataFrame.from_records(results[:], columns=field_names)
        elif self.use_api:
            response = requests.get(self.api_endpoint + f"?sql_query={sql}&format=csv")
            data = io.StringIO(response.text)
            df = pd.read_csv(data)
            for col in [c for c in df.columns if "_date" in c or "date_" in c]:
                df[col] = pd.to_datetime(df[col], errors="ignore")
            df = df[[c for c in df.columns if not "Unnamed: " in c]]
        return df

    def run_query_for_drillholes(self, sql, dh_nos):
        """Run query and use SQL template to inject/iterate over drillholes.

        Args:
            sql (str): SQL query with "{DH_NO}" where we want to inject drillhole numbers
            dh_nos (sequence of int): drillhole numbers

        Returns:
            panda.DataFrame

        """
        logger.debug(f"Running SQL on dh_nos={dh_nos}")
        dfs = []
        query = SQL(sql, dh_no=dh_nos)
        query.chunksize = 1000
        for subquery in query:
            dfs.append(self.query(subquery))
        return pd.concat(dfs)


def linear_trend(df, x=False, y=False, direction="normal"):
    """Calculate a linear trend.

    Args:
        df (pandas.DataFrame): Contains the timestamps for data points,
            and the data points themselves.
        x (str): Column which contains timestamps
        y (str): Column which contains numerical data for the linear regression
        direction (str): Either "normal" or "reverse". This determines whether
            an increase in the y value means "rising" or "declining". For example,
            for data which is "depth to water" (DTW or SWL) then you will want
            ``direction="reverse"``, because a numerically increasing DTW means
            that the parameter is declining. For RSWL you will want the default
            ``direction="normal"``.

    Returns:
        pandas.DataFrame: The data returned has the same shape as **df**, with
        any null values in **y** removed. The index is the x value from
        **x** in **df**. The columns are:

        - **y** (i.e. if ``y="swl"`` this column will be "swl"): the y values
        - trendline (float): the predicted y-value (i.e. on the trend line)
        - slope_yr (float): slope of trendline in units of **y** per year
        - slope_pct_0_yr (float): slope of trendline in percentage units, compared
          to the initial value i.e. the first y value.
        - slope_pct_mean_yr (float): slope of trend line in percentage units,
          compared to the mean of all y-values.
        - ``f"{y}_0"`` (float): the initial y-value.
        - ``f"{y}_mean"`` (float): the mean of all y values.
        - y_int (float): the y-intercept
        - slope_word_sal (str): either "Increasing" or "Decreasing"
        - slope_word_wl (str): either "Rising" or "Declining"

    """
    df_c = df.copy()

    if x in df_c.columns:
        df_c = df_c.dropna(subset=[x], how="any")
    else:
        df_c = df_c[df_c.index.notnull()]

    df_c = df_c.dropna(subset=[y], how="any")

    if x is False:
        x_values == df_c.index.values
    else:
        x_values = df_c[x]

    y_values = df_c[y].values
    x_values == df_c.index.values
    x_ts = [pd.Timestamp(xi) for xi in x_values]
    x_dec_yrs = [ts.year + ts.dayofyear / 365.25 for ts in x_ts]
    m, c = np.polyfit(x_dec_yrs, y_values, deg=1)
    y_pred = [xi * m + c for xi in x_dec_yrs]

    slope_word_sal = "Stable"
    slope_word_wl = "Stable"
    if (m > 0 and direction == "normal") or (m < 0 and direction == "reverse"):
        slope_word_sal = "Increasing"
        slope_word_wl = "Rising"
    elif (m < 0 and direction == "normal") or (m > 0 and direction == "reverse"):
        slope_word_sal = "Decreasing"
        slope_word_wl = "Declining"

    df_r = pd.DataFrame(
        {
            y: y_values,
            f"trendline": y_pred,
            "slope_yr": m,
            "slope_pct_0_yr": m / y_values[0] * 100,
            "slope_pct_mean_yr": m / np.mean(y_values) * 100,
            f"{y}_0": y_values[0],
            f"{y}_mean": np.mean(y_values),
            f"y_int": c,
            "slope_word_sal": slope_word_sal,
            "slope_word_wl": slope_word_wl,
        },
        index=x_ts,
    )
    return df_r


def group_into_contiguous_months(s, short_year=False):
    """Group date data into a set of contiguous months i.e. monitoring rounds/programmes.

    Args:
        s (pd.Series): can be either timestamps already, or strings which will be
            converted into timestamps e.g. "2023-06", "2023-07"
        short_year (bool): if False use a long year for the labels e.g. "Oct 2025".
            If True use a short year e.g. "Oct 25".

    Returns:
        pandas.Series: A list of descriptive labels e.g. "Jan 2023", "Oct-Nov 2024", or
            "Dec 2023-Mar 2024" which group the data provided. The index is identical
            to **s**.

    """
    MONTHS = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    df2 = pd.DataFrame({"data": s}, index=s.index)
    df2["timestamp"] = pd.to_datetime(df2["data"])
    df2["original_index"] = df2.index
    df2 = df2.sort_values("timestamp")
    df2["diff"] = df2.timestamp.diff()
    df2["separate"] = df2["diff"] > pd.Timedelta(days=31)
    df2["group"] = pd.NA
    group = 0
    for idx, row in df2.iterrows():
        if row.separate:
            group += 1
        df2.loc[idx, "group"] = group
    df2["group_desc"] = ""
    for group_no, gdf in df2.groupby("group"):
        years = sorted(gdf.timestamp.dt.year.unique())
        if short_year:
            label_years = [str(y)[-2:] for y in years]
        else:
            label_years = years
        month_from = gdf.timestamp.dt.month.min()
        month_to = gdf.timestamp.dt.month.max()
        if len(years) == 1:
            months = sorted(gdf.timestamp.dt.month.unique())
            if len(months) == 1:
                desc = f"{MONTHS[months[0]]} {years[0]}"
            elif len(months) > 1:
                desc = f"{MONTHS[month_from]}-{MONTHS[month_to]} {years[0]}"
        elif len(years) > 1:
            month_from = gdf[gdf.timestamp.dt.year == years[0]].timestamp.dt.month.min()
            month_to = gdf[gdf.timestamp.dt.year == years[-1]].timestamp.dt.month.min()
            desc = f"{MONTHS[month_from]} {years[0]}-{MONTHS[month_to]} {years[-1]}"
        df2.loc[df2.group == group_no, "group_desc"] = desc
    df2 = df2.sort_values("original_index")
    return pd.Series(df2.group_desc)


def unit_hyphen_to_long(h):
    """Convert unit number to integer format.

    Args:
        h (str): unit number in any format. See :class:`sa_gwdata.UnitNumber`

    Returns:
        integer or None: unit number in integer format e.g. 662800124

    """
    u = UnitNumber(h)
    return u.long_int


def unit_long_to_hyphen(l):
    """Convert unit number to hyphenated format.

    Args:
        h (str): unit number in any format. See :class:`sa_gwdata.UnitNumber`

    Returns:
        str: unit number in hyphenated format e.g. 6628-124

    """
    u = UnitNumber(l)
    return u.hyphen


def make_dh_title(well, elements=("unit_no", "obs_no", "dh_name")):
    data = dict(
        dh_no=f"DH {well.dh_no}",
        unit_no=str(well.unit_hyphen).replace("None", ""),
        obs_no=str(well.obs_no).replace("None", ""),
        dh_name=str(well.dh_name).replace("None", ""),
        aquifer=str(well.aquifer).replace("None", ""),
    )
    components = [data[x] for x in elements]
    valid_components = [c for c in components if c]
    if len(valid_components) == 0:
        valid_components = [data["dh_no"]]
    title = " / ".join(valid_components)
    if data["aquifer"]:
        title += f" ({data['aquifer']})"
    return title
