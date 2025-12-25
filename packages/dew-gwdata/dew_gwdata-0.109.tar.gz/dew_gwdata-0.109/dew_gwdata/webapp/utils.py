from datetime import datetime
from pathlib import Path
import sqlite3
import logging

import pandas as pd
import ausweather

import dew_gwdata as gd

logger = logging.getLogger(__name__)


def prep_table_for_html(df, cols=None, set_index=None, query=None, env="prod"):
    """Prepare table for conversion to HTML and presentation as a list of wells.

    Args:
        - df (pd.DataFrame): data to prepare. Should have all the standard well ID columns
          "dh_no", "dh_name", "aquifer", "unit_hyphen", "obs_no", "class_all"
        - cols (sequence of string): If provided, these are the columns which,
          in addition to the standard columns used to present the well's ID, will
          be included. The standard ID columns are "title", "dh_no", "dh_name",
          "aquifer", and the generated columns (generated here) "suburb" and "rf_site".
        - set_index (None, "auto", or sequence of string): if None, the dataframe
          will be returned for a sequential integer index. If "auto", the standard
          well ID columns described above will be used to set the index. If provided,
          those columns will, ***in addition to the standard well ID columns***, be used
          to set an index.
        - query (Query object from starlette) - used to carry over URL parameters needed
          for the hyperlink on the "title" column relating to the SA Geodata environment.
        - env (bool): if query is not provided, this will be used instead.

    Returns:
        pandas.DataFrame: ready to conversion to HTML using :func:`frame_to_html`.

    """
    if cols is None:
        cols = list(df.columns)
    logger.debug(f"prepping table of length: {len(df)}")
    if len(df) == 0:
        empty_cols = list(df.columns)
        empty_cols.insert(0, "title")
        empty_cols.insert(6, "suburb")
        empty_cols.insert(7, "rf_site")
        empty_cols = [c for c in empty_cols if not c in ["unit_hyphen", "obs_no"]]
        return pd.DataFrame(columns=empty_cols)

    for idx, well in df.reset_index().iterrows():
        query_params = [f"dh_no={well.dh_no:.0f}"]
        dh_query_params = "&".join(query_params)
    if not query is None:
        env = query.env

    id_cols = ["title", "dh_no", "dh_name", "aquifer", "suburb", "rf_site"]
    final_cols = id_cols + cols

    df["title"] = df.apply(
        lambda well: (
            f'<nobr><a href="/app/well_summary?dh_no={well.dh_no}&env={env}">'
            f'{make_dh_title(well, elements=("unit_no", "obs_no"))}</a></nobr>'
        ),
        axis=1,
    )
    df["title"] = df.title.fillna("")
    df["suburb"] = gd.locate_wells_in_suburbs(df)
    df["rf_site"] = df.unit_hyphen.apply(
        lambda n: f"<a href='/app/rainfall_stations?nearest_to_well={n}'><img src='/static/external-link.svg' width=12 height=12 /></a>"
    )
    if "aquifer" in df.columns:
        df["aquifer"] = df.apply(
            lambda row: (
                f"<a href='/app/aquifer_unit?aquifer_code={row.aquifer}&env={env}'>{row.aquifer}</a>"
                if row.aquifer
                else ""
            ),
            axis=1,
        )
        df["aquifer"] = df.aquifer.fillna("")

    if "dh_name" in df:
        df["dh_name"] = df.dh_name.fillna("")

    available_id_cols = [c for c in id_cols if c in df.columns]
    available_final_cols = [c for c in final_cols if c in df.columns]

    final_df = df[available_final_cols]
    if set_index is None:
        return final_df
    elif set_index == "auto":
        return final_df.set_index(available_id_cols)
    else:
        available_extra_index_cols = [c for c in set_index if c in df.columns]
        return final_df.set_index(available_id_cols + available_extra_index_cols)


def make_dh_title(well, elements=("unit_no", "obs_no", "dh_name"), db=None):
    # The primary identifier should be the hyphenated unit number, unless
    # it does not exist, then the drillhole should be used.
    first_component = well.unit_hyphen
    if not first_component:
        first_component = well.dh_no

    # Include the well classification if it is anything other than
    # purely a water well.
    if "class_all" in well.index:
        if well.class_all != "WW":
            class_string = well.class_all
            if "WP" in well.class_all:
                class_string += f"({well.water_point_type})"
            first_component += " " + class_string

    other_components = [well[element] for element in elements[1:] if well[element]]

    name_string = " / ".join([first_component] + other_components)

    # Append the aquifer if it is assigned.
    if well["aquifer"]:
        title = name_string + f" ({well['aquifer']})"
    else:
        title = name_string

    # data = dict(
    #     dh_no=f"DH {well.dh_no}",
    #     unit_no=str(well.unit_hyphen).replace("None", ""),
    #     obs_no=str(well.obs_no).replace("None", ""),
    #     dh_name=str(well.dh_name).replace("None", ""),
    #     aquifer=str(well.aquifer).replace("None", ""),
    # )
    # components = [data[x] for x in elements]
    # valid_components = [c for c in components if c]
    # if len(valid_components) == 0:
    #     valid_components = [data["dh_no"]]
    # title = " / ".join(valid_components)
    # if data["aquifer"]:
    #     title += f" ({data['aquifer']})"
    # if data["class_all"]:
    #     title += f" {data['class_all']}"
    return title


def format_datetime(dt):
    try:
        tstamp = pd.Timestamp(dt)
    except:
        return dt
    else:
        if pd.isnull(tstamp):
            return ""
        else:
            if tstamp.hour == tstamp.minute == tstamp.second == 0:
                return tstamp.strftime("%d/%m/%Y")
            else:
                return tstamp.strftime("%d/%m/%Y %H:%M:%S")


def frame_to_html(
    df,
    transpose_last=False,
    apply=None,
    apply_kws=None,
    remove_col_underscores=True,
    bold_rows=False,
    add_username_links=True,
    **kwargs,
):
    if apply_kws is None:
        apply_kws = {}
    if remove_col_underscores:
        df.columns = [str(c).replace("_", " ") for c in df.columns]
    for col in df.columns:
        if "date" in col:
            df[col] = df[col].apply(lambda v: f"<nobr>{format_datetime(v)}</nobr>")
        if col in ("unit hyphen", "unit no"):
            df[col] = df[col].apply(lambda v: f"<nobr>{v}</nobr>")
    df = df.fillna("")
    kwargs["escape"] = False
    if add_username_links:
        url = "/app/schema_data?owner=DHDB&table_name=MS_USER_VW&limit=200&filter_by=&select=*&where=user_code%3D%27{username}%27&order_by=&env=prod&transpose=Y"
        for col in df.columns:
            if col.endswith("_by") or col.endswith(" by"):
                df[col] = df[col].apply(
                    lambda v: f"<a href='{url.format(username=v)}'>{v}</a>"
                )

    if transpose_last:
        df = df.T
    df = df.map(lambda s: s.replace("\n", "<br />") if isinstance(s, str) else s)
    df = df.map(lambda s: s.replace("\n", "<br />") if isinstance(s, str) else s)

    if apply is None:
        table_html = df.to_html(classes="", bold_rows=bold_rows, **kwargs)
    else:
        if "subset" in apply_kws:
            apply_kws["subset"] = [col.replace("_", " ") for col in apply_kws["subset"]]

        styler = df.style.apply(apply, **apply_kws)
        table_html = styler.to_html(bold_rows=bold_rows)
    return "<div class='table-outer-wrapper'>" + table_html + "</div>"


def series_to_html(s, transpose=True, **kwargs):
    assert isinstance(s, pd.Series)
    df = s.to_frame()
    if transpose:
        df = df.T
    return frame_to_html(df, transpose_last=True, **kwargs)


import numpy as np

BASE_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-~_"


def to_deltas(arr):
    arr = np.asarray(arr)
    arr = np.sort(arr)
    return np.diff(arr, prepend=0)


def from_deltas(arr):
    return np.cumsum(arr)


def encode(n, characters):
    base = len(characters)
    result = []
    i = 0
    while n > 0:
        i += 1
        quotient = n // base
        remainder = n % base
        result.append(characters[remainder])
        n = quotient
    encoded = "".join(result[::-1])
    return encoded


def decode(s, characters):
    base = len(characters)
    n = 0
    for i, char in enumerate(s[::-1]):
        n += (base**i) * characters.index(char)
    return n


def dhnos_to_urlstr(dh_nos):
    deltas = to_deltas(dh_nos)
    encoded = [encode(d, BASE_CHARS) for d in deltas]
    return ".".join(encoded)


def urlstr_to_dhnos(url_str):
    decoded = [decode(s, BASE_CHARS) for s in url_str.split(".")]
    return from_deltas(decoded)


def fmt_for_js(x):
    if str(x).startswith("new Date("):
        return x
    elif isinstance(x, str):
        return '"' + x.replace('"', "'") + '"'
    elif x is None:
        return '""'
    elif pd.isnull(x):
        return ""
    else:
        return str(x)


# def open_db(fn=None):
#     """Open the local webapp database

#     Returns:
#         sqlite3.Connection: A database connection. You need to remember
#         to close it."""

#     if fn is None:
#         fn = Path(__file__).parent / "dew_gwdata.webapp.db"
#         logger.debug(f"opening db fn=None therefore fn={fn}")

#     create_table = """
#     CREATE TABLE IF NOT EXISTS "daily_rainfall" (
#     	"id"	TEXT UNIQUE,
#     	"station_id"	TEXT NOT NULL,
#     	"date"	TEXT NOT NULL,
#     	"rainfall"	REAL NOT NULL,
#     	"interpolated_code"	INTEGER NOT NULL,
#     	"quality"	INTEGER NOT NULL,
#         "date_added" TEXT NOT NULL
#     );
#     """
#     conn = sqlite3.connect(str(fn))
#     cursor = conn.cursor()
#     cursor.execute(create_table)
#     conn.commit()
#     return conn


def multiprocess_photo_zipfile(args, ret_dict):
    zfn = produce_photo_zip(args)
