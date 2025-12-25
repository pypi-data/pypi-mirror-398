import datetime
from pathlib import Path
import logging
import re

import pandas as pd
import networkx as nx
import pyodbc
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
import appdirs
import toml

import dew_gwdata as gd
from .gwdata import normalise_and_clean_logger_data, resample_logger_data
from .utils import *
from .webapp.config import WEB_APP_HOST, WEB_APP_PORT

logger = logging.getLogger(__name__)

SERVERS = {
    ("ts", "dev"): "https://envswimsd01.env.sa.gov.au",
    ("ts", "qa"): "https://envswimsq01.env.sa.gov.au",
    ("ts", "prod"): "https://timeseries.waterconnect.sa.gov.au:443",
    ("wp", "dev"): "https://envswimsd02.env.sa.gov.au",
    ("wp", "qa"): "https://envswimsq02.env.sa.gov.au",
    ("wp", "prod"): "https://webportal.waterconnect.sa.gov.au:443",
}

PARAM_SUBS_SAGD_TO_AQ = {
    "dtw": "Depth to Water",
    "swl": "SWL",
    "rswl": "RSWL",
    "ec": "EC Corr",
    "tds": "TDS from EC",
}

PARAM_SUBS_AQ_TO_SAGD = {v: k for k, v in PARAM_SUBS_SAGD_TO_AQ.items()}


def get_aquarius_users_filename():
    folder = Path(appdirs.user_data_dir("dew_gwdata", "DEW"))
    folder.mkdir(parents=True, exist_ok=True)
    filename = "aquarius_users.toml"
    path = folder / filename
    return path


def register_aq_password(user, password):
    """Register and store the password for an AQ TS/WP account."""
    path = get_aquarius_users_filename()
    if path.is_file():
        with open(path, "r") as f:
            data = toml.load(f)
    else:
        data = {}
    data[user] = password
    with open(path, "w") as f:
        toml.dump(data, f)
    return True


def get_password(user):
    """Fetch previously registered and stored AQ TS/WP user password."""
    folder = Path(appdirs.user_data_dir("dew_gwdata", "DEW"))
    filename = "aquarius_users.toml"
    path = folder / filename
    with open(path, "r") as f:
        data = toml.load(f)
        return data[user]


def convert_aq_timestamp(ts):
    """Convert an AQTS-style timestamp to a pandas.Timestamp.

    'Beginning of time' and 'End of time' are represented as None.

    Example::

        >>> convert_aq_timestamp("2011-11-28T09:15:27.0000000+00:00")
        Timestamp('2011-11-28 09:15:27')
        >>> convert_aq_timestamp("2011-11-28T09:15:27.0000000+00:00")
        None

    """
    if not ts or pd.isnull(ts):
        return None
    else:
        ts_sub = ts[:10] + ts[11:26] + ts[27:30] + ts[31:]
        ts_sub = ts_sub[:-5]
        if ts_sub[:4] == "0001":
            return None
        elif ts_sub[:4] == "9999":
            return None
        if "." in ts_sub:
            fmt = "%Y-%m-%d%H:%M:%S.%f"
        elif ts_sub.endswith(":"):
            fmt = "%Y-%m-%d%H:%M:"
        else:
            fmt = "%Y-%m-%d%H:%M:%S"
        return pd.Timestamp(datetime.datetime.strptime(ts_sub.strip("+"), fmt))


def format_iso8601(ts):
    offset = ts.strftime("%z")
    offset = offset[:3] + ":" + offset[3:]
    return ts.strftime("%Y-%m-%dT%H:%M:%S") + offset


class Endpoint:
    """Aquarius TS/WP API endpoint wrapper.

    Args:
        server (str): url
        prefix (str): API string
        verify_ssl (bool): e.g. False to ignore SSL errors - False by default
        kwargs: used for subsequent get/post requests

    """

    def __init__(self, server, prefix, verify_ssl=False, **kwargs):
        self.server = server
        self.prefix = prefix
        if ".env.sa.gov.au" in self.server or verify_ssl is False:
            default_verify = False
        else:
            default_verify = True
        self.kwargs = {"verify": default_verify}
        self.kwargs.update(kwargs)

    def make_path(self, path):
        return self.server + self.prefix + path

    def make_kwargs(self, **kwargs):
        result = dict(self.kwargs)
        result.update(kwargs)
        return result

    def get(self, path, *args, **kwargs):
        path = self.make_path(path)
        kwargs = self.make_kwargs(**kwargs)
        return requests.get(path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        path = self.make_path(path)
        kwargs = self.make_kwargs(**kwargs)
        return requests.post(path, *args, **kwargs)


def convert_GetLocationData_to_series(respdata):
    """Convert the output of GetLocationData (TS Publish API) to a flat structure.

    Returns: pandas Series

    """
    key_renames = {
        "Identifier": "loc_id",
        "LocationName": "loc_name",
        "Description": "loc_descr",
        "UniqueId": "loc_uid",
        "LocationType": "loc_type",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Elevation": "elev",
    }
    values = {v: respdata[k] for k, v in key_renames.items()}
    for ext_attr in respdata["ExtendedAttributes"]:
        values[ext_attr["Name"]] = ext_attr.get("Value", None)
    return pd.Series(values)


def convert_GetTimeseriesMetadata_to_series(respdata):
    key_renames = {
        "Identifier": "ts_id",
        "TimeSeriesType": "ts_type",
        "LocationIdentifier": "loc_id",
        "Parameter": "param",
        "Label": "label",
        "RawStartTime": "raw_start_time",
        "RawEndTime": "raw_end_time",
        "CorrectedStartTime": "corr_start_time",
        "CorrectedEndTime": "corr_end_time",
        "Description": "descr",
        "Comment": "comment",
        "Publish": "published",
        "Unit": "unit",
        "UtcOffset": "utc_offset",
        "LastModified": "modified_date",
        "ComputationIdentifier": "computation_id",
        "ComputationPeriodIdentifier": "computation_pd_id",
        "SubLocationIdentifier": "subloc_id",
        "UniqueId": "ts_uid",
    }
    values = {v: respdata.get(k, None) for k, v in key_renames.items()}
    for ext_attr in respdata["ExtendedAttributes"]:
        values[ext_attr["Name"]] = ext_attr.get("Value", None)
    return pd.Series(values)


def identify_aq_locations(text, normalize_case=True, aq=None, env="prod", **kwargs):
    if aq is None:
        aq = DEWAquarius(env=env)
    aq_locs = aq.find_locations(**kwargs)
    aq_locids = aq_locs.loc_id.values
    aq_locnames = aq_locs.loc_name.values
    text = text.replace("\n", " ")
    if normalize_case:
        text = text.upper()
        aq_locids = [locid.upper() for locid in aq_locids]
        aq_locnames = [name.upper() for name in aq_locnames]
    locs = []
    for item in text.split():
        if item in aq_locids:
            locs.append(item)
        elif item in aq_locnames:
            locs.append(aq_locids[aq_locnames.index(item)])
    return list(set(locs))


class DEWAquariusServer:
    """Wrapper for Aquarius server application API.

    Args:
        app (str): either "ts" or "wp"
        env (str): either "dev", "qa", or "prod"
        auth (str or HttpBasicAuth): if a string, it will look up the password
            previously stored using dew_gwdata.register_aq_password()

    """

    def __init__(self, app="ts", env="prod", auth="timeseries"):
        app = app.lower()
        env = env.lower()

        if "prod" in app:
            env = "prod"
        elif "qa" in app:
            env = "qa"
        elif "dev" in app:
            env = "dev"

        if "ts" in app or "time series" in app or "timeseries" in app:
            app = "ts"
        elif "wp" in app or "portal" in app:
            app = "wp"

        self.app = app
        self.env = env
        self.server = SERVERS[(app, env)]
        if app == "ts":
            if isinstance(auth, str):
                auth = HTTPBasicAuth(auth, get_password(auth))
            self.acquisition = Endpoint(
                self.server, "/AQUARIUS/Acquisition/v1/", auth=auth
            )
            self.provisioning = Endpoint(
                self.server, "/AQUARIUS/Provisioning/v2/", auth=auth
            )
            self.publish = Endpoint(self.server, "/AQUARIUS/Publish/v2/", auth=auth)


class DEWAquarius:
    """Wrapper for Aquarius application APIs.

    Args:
        env (str): either "dev", "qa", or "prod"
        ts_auth (str or HttpBasicAuth): Authentication to use for Time Series.
            if a string, it will look up the password
            previously stored using dew_gwdata.register_aq_password()
        wp_auth (str or HttpBasicAuth): Authentication to use for Web Portal.
            if a string, it will look up the password
            previously stored using dew_gwdata.register_aq_password()

    """

    def __init__(
        self, env="prod", ts_auth="timeseries", wp_auth="apireader", cache_conn=None
    ):
        self.ts = DEWAquariusServer(app="ts", env=env, auth=ts_auth)
        self.wp = DEWAquariusServer(app="wp", env=env, auth=wp_auth)
        self.env = env
        self.cache_conn = cache_conn

    def find_locations(self, locid="", name="", from_cache=False, **kwargs):
        """Find locations in AQTS by matching against location attributes.

        Keyword Arguments:
            locid (str): wildcard pattern match against location identifiers
            name (str): wildcard pattern match against location names

        Returns: pandas DataFrame with columns:
            - loc_name
            - loc_id
            - loc_uid
            - folder
            - modified_date
            - publish
            - tags

        Uses the Publish API GetLocationDescriptionList and maps the following
        keys across:

            - "Name" becomes "loc_name"
            - "Identifier" becomes "loc_id"
            - "UniqueId" becomes "loc_uid"
            - "IsExternalLocation" is dropped
            - "PrimaryFolder" becomes "folder"
            - "SecondaryFolder" is dropped
            - "LastModified" becomes "modified_date"
            - "Publish" becomes "publish"
            - "Tags" is replaced by a semicolon-separated string of *TagKey: TagValue*

        """
        kwargs["LocationIdentifier"] = kwargs.get("LocationIdentifier", locid)
        kwargs["LocationName"] = kwargs.get("LocationName", name)
        if from_cache:
            return self._find_locations_from_cache(kwargs)
        else:
            return self._find_locations_from_api(kwargs)

    def _find_locations_from_cache(self, kwargs):
        locid = kwargs["LocationIdentifier"]
        name = kwargs["LocationName"]
        table = f"aq_{self.env}_locations"
        query = f"""select loc_id, 
                           loc_name, 
                           folder, 
                           publish, 
                           modified_date, 
                           tags, 
                           loc_uid 
                    from {table}"""
        if locid:
            query += f"""
                    where loc_id like '{locid.replace('*', '%')}'
            """
        elif name:
            query += f"""
                    where loc_name like '{name.replace('*', '%')}'
            """
        return pd.read_sql(query, self.cache_conn)

    def _find_locations_from_api(self, kwargs):
        resp = self.ts.publish.get("GetLocationDescriptionList", params=kwargs)
        df = pd.json_normalize(resp.json()["LocationDescriptions"])
        if len(df) == 0:
            df = pd.DataFrame(
                columns=[
                    "Name",
                    "Identifier",
                    "UniqueId",
                    "PrimaryFolder",
                    "LastModified",
                    "Publish",
                    "Tags",
                ]
            )
        df["tags"] = df.Tags
        # df["tags"] = "JIRA GD-10"
        # df.loc[:, "tags"] = [
        #     "|".join([t["Key"] + ":" + t["Value"] for t in tag_list])
        #     for tag_list in df.Tags
        # ]
        df = df[[c for c in df.columns if not c in ("Tags", "IsExternalLocation")]]
        df = df.rename(
            columns={
                "Name": "loc_name",
                "Identifier": "loc_id",
                "UniqueId": "loc_uid",
                "PrimaryFolder": "folder",
                "LastModified": "modified_date",
                "Publish": "publish",
                "tags": "tags",
            }
        )
        df = df[
            [
                "loc_id",
                "loc_name",
                "folder",
                "publish",
                "modified_date",
                "tags",
                "loc_uid",
            ]
        ]
        df["modified_date"] = pd.to_datetime(
            df.modified_date.str[:19],  # + df.modified_date.str[-6:],
            format="%Y-%m-%dT%H:%M:%S",  # %z
        )
        return df

    def fetch_single_location_data(self, locid, from_cache=False):
        """Fetch location attribute data for a single location identifier.

        Returns: pandas Series (unwraps extended attributes and discards unneeded
            response metadata).

        """
        if from_cache:
            return self._fetch_single_location_data_from_cache(locid=locid)
        else:
            return self._fetch_single_location_data_from_api(locid=locid)

    def _fetch_single_location_data_from_cache(self, locid):
        table = f"aq_{self.env}_locations"
        query = f"select * from {table} where loc_id = '{locid}'"
        df = pd.read_sql(query, self.cache_conn)
        if len(df):
            return df.iloc[0]
        else:
            raise KeyError(f"loc_id {locid} not found in cache")

    def _fetch_single_location_data_from_api(self, locid):
        resp = self.ts.publish.get(
            "GetLocationData", params={"LocationIdentifier": locid}
        )
        return convert_GetLocationData_to_series(resp.json())

    def fetch_locations_data(self, locids=None, from_cache=False, **kwargs):
        """Fetch location attribute data for multiple locations.

        Keyword Arguments:
            locids (list, optional): list of location identifiers

        If you do not pass *locids*, you can instead pass any arguments here which you
        would otherwise use with DEWAquarius.find_locations().

        Returns: pandas DataFrame

        """
        if locids is None:
            loc_df = self.find_locations(from_cache=from_cache, **kwargs)
        else:
            loc_dfs = []
            for locid in locids:
                loc_dfs.append(self.find_locations(locid=locid, from_cache=from_cache))
            loc_df = pd.concat(loc_dfs)
        locids = loc_df.loc_id.unique()
        series = []
        for locid in locids:
            logger.debug(f"fetching location metadata for {locid}")
            try:
                series.append(
                    self.fetch_single_location_data(locid, from_cache=from_cache)
                )
            except KeyError:
                pass
        df = pd.DataFrame(series)
        left = loc_df[["loc_uid", "publish", "folder", "modified_date", "tags"]]
        right = df[
            [c for c in df.columns if (not c in left.columns) or (c == "loc_uid")]
        ]
        prefix_cols = [
            "loc_id",
            "loc_name",
            "loc_type",
            "loc_descr",
            "publish",
            "folder",
            "tags",
            "modified_date",
            "latitude",
            "longitude",
            "elev",
        ]
        suffix_cols = ["loc_uid"]
        if len(left) > 0 and len(right) > 0:
            xdf = pd.merge(left, right, left_on="loc_uid", right_on="loc_uid")
            xdf_upper_cols = [c for c in xdf.columns if c.upper() == c]
            xdf = xdf[prefix_cols + xdf_upper_cols + suffix_cols]
            return xdf
        else:
            return pd.DataFrame(columns=prefix_cols + suffix_cols)

    def fetch_locations_timeseries_metadata(self, locids, from_cache=False):
        if from_cache:
            df = self._fetch_locations_timeseries_metadata_from_cache(locids=locids)
        else:
            df = self._fetch_locations_timeseries_metadata_from_api(locids=locids)
        return df

    def _fetch_single_location_timeseries_metadata_from_api(self, locid):
        logger.debug(f"Fetching single location timeseries metadata for {locid}")
        resp = self.ts.publish.get(
            "GetTimeSeriesDescriptionList", params={"LocationIdentifier": locid}
        )
        df = pd.DataFrame(
            [
                convert_GetTimeseriesMetadata_to_series(r)
                for r in resp.json().get("TimeSeriesDescriptions", [])
            ]
        )
        prefix_cols = [
            "ts_id",
            "ts_type",
            "loc_id",
            "param",
            "label",
            "label_0",
            "raw_start_time",
            "raw_end_time",
            "corr_start_time",
            "corr_end_time",
            "descr",
            "comment",
            "published",
            "unit",
            "modified_date",
        ]
        suffix_cols = [
            "utc_offset",
            "computation_id",
            "computation_pd_id",
            "subloc_id",
            "ts_uid",
        ]
        if len(df) == 0:
            df = pd.DataFrame(columns=prefix_cols + suffix_cols)
        df["label_0"] = [x.split("--", 1)[0] for x in df["label"]]
        for dt_col in [
            "modified_date",
            "raw_start_time",
            "raw_end_time",
            "corr_start_time",
            "corr_end_time",
        ]:
            df[dt_col] = pd.to_datetime(
                df[dt_col].str[:19],
                format="%Y-%m-%dT%H:%M:%S",  # %z
            )
        upper_cols = [c for c in df.columns if c.upper() == c]
        return df[prefix_cols + upper_cols + suffix_cols]

    def _fetch_locations_timeseries_metadata_from_cache(self, locids):
        table = f"aq_{self.env}_timeseries_metadata"
        qarg = "(" + ",".join([f"'{l}'" for l in locids]) + ")"
        query = f"select * from {table} where loc_id in {qarg}"
        df = pd.read_sql(query, self.cache_conn)
        prefix_cols = [
            "ts_id",
            "ts_type",
            "loc_id",
            "param",
            "label",
            "label_0",
            "raw_start_time",
            "raw_end_time",
            "corr_start_time",
            "corr_end_time",
            "descr",
            "comment",
            "published",
            "unit",
            "modified_date",
        ]
        suffix_cols = [
            "utc_offset",
            "computation_id",
            "computation_pd_id",
            "subloc_id",
            "ts_uid",
        ]
        if len(df) == 0:
            df = pd.DataFrame(columns=prefix_cols + suffix_cols)
        df["label_0"] = [x.split("--", 1)[0] for x in df["label"]]
        for dt_col in [
            "modified_date",
            "raw_start_time",
            "raw_end_time",
            "corr_start_time",
            "corr_end_time",
        ]:
            df[dt_col] = pd.to_datetime(
                df[dt_col].str[:19],
                format="%Y-%m-%dT%H:%M:%S",  # %z
            )
        upper_cols = [c for c in df.columns if c.upper() == c]
        return df[prefix_cols + upper_cols + suffix_cols]

    def _fetch_locations_timeseries_metadata_from_api(self, locids):
        dfs = []
        for locid in locids:
            dfs.append(self._fetch_single_location_timeseries_metadata_from_api(locid))
        df = pd.concat(dfs)
        prefix_cols = [
            "ts_id",
            "ts_type",
            "loc_id",
            "param",
            "label",
            "raw_start_time",
            "raw_end_time",
            "corr_start_time",
            "corr_end_time",
            "descr",
            "comment",
            "published",
            "unit",
            "modified_date",
        ]
        suffix_cols = [
            "utc_offset",
            "computation_id",
            "computation_pd_id",
            "subloc_id",
            "ts_uid",
        ]
        upper_cols = [c for c in df.columns if c.upper() == c]
        return df[prefix_cols + upper_cols + suffix_cols]

    def fetch_timeseries_relatives(self, ts_uid):
        """Fetch downchain (child) and upchain (parent) timeseries for a given timeseries.
        
        Args:
            ts_uid (str): time series unique ID.
            
        Returns: pandas DataFrame with columns as below::
        
                                queried_ts_uid                      input_ts_uid  \
            0  084a3a7aacc84da3b3e48314b83b5f7e  084a3a7aacc84da3b3e48314b83b5f7e   
            1  084a3a7aacc84da3b3e48314b83b5f7e  7fa0d97e051e47a9b822e41705b27ba1   
            2  084a3a7aacc84da3b3e48314b83b5f7e  1206677b0bf34dc29d4a23495597d3fb   

            input_ts_order   processor_type  \
            0               1      calculation   
            1               1  fillmissingdata   
            2               2  fillmissingdata   

                                                    description start_time end_time  \
            0                                                          None     None   
            1  Wait for a gap in the primary feed, then start...       None     None   
            2  Wait for a gap in the primary feed, then start...       None     None   

                                                settings.formula settings.master  \
            0  y = Math.Round((0.548 * x1) + (2.2 * Math.Pow(...               1   
            1                                                NaN             NaN   
            2                                                NaN             NaN   

            settings.data_edge_tolerance settings.output_tolerance  \
            0                          NaN                       NaN   
            1                         PT0S               MaxDuration   
            2                         PT0S               MaxDuration   

                                output_ts_uid relationship_to_queried_ts  
            0  ff2e7cf830094f82845409b74e81c7ef                      child  
            1  084a3a7aacc84da3b3e48314b83b5f7e                     parent  
            2  084a3a7aacc84da3b3e48314b83b5f7e                     parent  

        
        """
        children_json = self.ts.publish.get(
            "GetDownchainProcessorListByTimeSeries",
            params={"TimeSeriesUniqueId": ts_uid},
        ).json()
        parents_json = self.ts.publish.get(
            "GetUpchainProcessorListByTimeSeries", params={"TimeSeriesUniqueId": ts_uid}
        ).json()
        processors = []
        for relationship, response in [
            ("child", children_json),
            ("parent", parents_json),
        ]:
            for pr in response.get("Processors", []):
                for input_ts_order, input_ts in enumerate(
                    pr["InputTimeSeriesUniqueIds"]
                ):
                    output_ts = pr["OutputTimeSeriesUniqueId"]
                    period = pr.get("ProcessorPeriod", {})
                    settings = pr.get("Settings", {})
                    proc = {
                        "queried_ts_uid": ts_uid,
                        "input_ts_uid": input_ts,
                        "input_ts_order": input_ts_order + 1,
                        "processor_type": pr["ProcessorType"],
                        "description": pr.get("Description", ""),
                        "start_time": period.get("StartTime", ""),
                        "end_time": period.get("EndTime", ""),
                        "output_ts_uid": output_ts,
                        "relationship_to_queried_ts": relationship,
                    }
                    for key, value in settings.items():
                        dict_key = f"settings.{gd.camel_to_underscore(key)}"
                        proc[dict_key] = value

                    for key in ["start_time", "end_time"]:
                        if proc[key]:
                            proc[key] = convert_aq_timestamp(proc[key])
                    processors.append(proc)
        df = pd.DataFrame(processors)
        if len(df) == 0:
            df = pd.DataFrame(
                columns=[
                    "queried_ts_uid",
                    "input_ts_uid",
                    "processor_type",
                    "description",
                    "start_time",
                    "end_time",
                    "output_ts_uid",
                    "relationship_to_queried_ts",
                ]
            )

        # Reorder columns.
        end_cols = ["output_ts_uid", "relationship_to_queried_ts"]
        cols = [c for c in df.columns if not c in end_cols] + end_cols
        return df[cols]

    def fetch_timeseries_relationships_for_location(
        self,
        locid=None,
        timeseries_metadata=None,
        ts_id_type="uid",
        include_queried_ts_info=False,
        **kwargs,
    ):
        """Fetch the relationships between all time series at a location.
        
        Args:
            locid (str or None): location to look at.
            timeseries_metadata (pd.DataFrame or None): if this is None, it will be retrieved
                for *locid* using :meth:`dew_gwdata.DEWAquarius.fetch_locations_timeseries_metadata`.
            ts_id_type (str): the type of ID field to use for time series. One of 'uid', 'param_label'
                or 'both'.
            include_queried_ts_info (bool): include information in the dataframe on where the data
                came from in terms of the upchain/downchain API query. Should only be needed for
                debugging.
        
        Other keyword arguments will be passed to :meth:`dew_gwdata.DEWAquarius.fetch_locations_timeseries_metadata`
        if *timeseries_metadata* is None.
        
        Returns: pandas DataFrame with columns as in the examples below::
        
                                    input_ts_param_label  input_ts_order  \
            0                      EC Corr.Best Available             1.0   
            1                  EC Corr.Combined Corrected             1.0   
            2                               EC Corr.Telem             2.0   
            3                       Water Pressure.Master             1.0   
            4   Depth to Water.Best Available--Continuous             1.0   
            5   Depth to Water.Best Available--Continuous             1.0   
            6                               Voltage.Telem             1.0   
            7                       Depth to Water.Master             1.0   
            8                        Depth to Water.Telem             2.0   
            9                            EC Uncorr.Master             1.0   
            10                            EC Uncorr.Telem             2.0   
            11                          Water Temp.Master             1.0   
            12                           Water Temp.Telem             2.0   
            13                             EC Corr.Master             1.0   
            14                                EC Corr.FLY             2.0   
            15                           EC Uncorr.Master             1.0   
            16                          Water Temp.Master             2.0   

                    processor_type                                        description  \
            0          calculation                                                      
            1    fill missing data  Wait for a gap in the primary feed, then start...   
            2    fill missing data  Wait for a gap in the primary feed, then start...   
            3   corr. pass through                                                      
            4     datum conversion                                                      
            5     datum conversion                                                      
            6   corr. pass through                                                      
            7    fill missing data  Wait for a gap in the primary feed, then start...   
            8    fill missing data  Wait for a gap in the primary feed, then start...   
            9    fill missing data  Wait for a gap in the primary feed, then start...   
            10   fill missing data  Wait for a gap in the primary feed, then start...   
            11   fill missing data  Wait for a gap in the primary feed, then start...   
            12   fill missing data  Wait for a gap in the primary feed, then start...   
            13   fill missing data  Wait for a gap in the primary feed, then start...   
            14   fill missing data  Wait for a gap in the primary feed, then start...   
            15         calculation                                                      
            16         calculation                                                      

            start_time end_time                                   settings.formula  \
            0        None     None  y = Math.Round((0.548 * x1) + (2.2 * Math.Pow(...   
            1        None     None                                                NaN   
            2        None     None                                                NaN   
            3        None     None                                                NaN   
            4        None     None                                                NaN   
            5        None     None                                                NaN   
            6        None     None                                                NaN   
            7        None     None                                                NaN   
            8        None     None                                                NaN   
            9        None     None                                                NaN   
            10       None     None                                                NaN   
            11       None     None                                                NaN   
            12       None     None                                                NaN   
            13       None     None                                                NaN   
            14       None     None                                                NaN   
            15       None     None                y = (1/(1 + 0.02 * (x2 - 25))) * x1   
            16       None     None                y = (1/(1 + 0.02 * (x2 - 25))) * x1   

            settings.master settings.data_edge_tolerance settings.output_tolerance  \
            0                1                          NaN                       NaN   
            1              NaN                         PT0S               MaxDuration   
            2              NaN                         PT0S               MaxDuration   
            3              NaN                          NaN                       NaN   
            4              NaN                          NaN                       NaN   
            5              NaN                          NaN                       NaN   
            6              NaN                          NaN                       NaN   
            7              NaN                         PT0S               MaxDuration   
            8              NaN                         PT0S               MaxDuration   
            9              NaN                         PT0S               MaxDuration   
            10             NaN                         PT0S               MaxDuration   
            11             NaN                         PT0S               MaxDuration   
            12             NaN                         PT0S               MaxDuration   
            13             NaN                         PT0S               MaxDuration   
            14             NaN                         PT0S               MaxDuration   
            15               1                          NaN                       NaN   
            16               1                          NaN                       NaN   

                                    output_ts_param_label settings.method settings.source  \
            0                  TDS from EC.Best Available             NaN             NaN   
            1                      EC Corr.Best Available             NaN             NaN   
            2                      EC Corr.Best Available             NaN             NaN   
            3               Water Pressure.Best Available             NaN             NaN   
            4                         RSWL.Best Available     DefaultNone            8170   
            5                          SWL.Best Available     DefaultNone            8170   
            6                      Voltage.Best Available             NaN             NaN   
            7   Depth to Water.Best Available--Continuous             NaN             NaN   
            8   Depth to Water.Best Available--Continuous             NaN             NaN   
            9        EC Uncorr.Best Available--Continuous             NaN             NaN   
            10       EC Uncorr.Best Available--Continuous             NaN             NaN   
            11      Water Temp.Best Available--Continuous             NaN             NaN   
            12      Water Temp.Best Available--Continuous             NaN             NaN   
            13                 EC Corr.Combined Corrected             NaN             NaN   
            14                 EC Corr.Combined Corrected             NaN             NaN   
            15                                EC Corr.FLY             NaN             NaN   
            16                                EC Corr.FLY             NaN             NaN   

            settings.target_datum  
            0                    NaN  
            1                    NaN  
            2                    NaN  
            3                    NaN  
            4                    AHD  
            5                    NaN  
            6                    NaN  
            7                    NaN  
            8                    NaN  
            9                    NaN  
            10                   NaN  
            11                   NaN  
            12                   NaN  
            13                   NaN  
            14                   NaN  
            15                   NaN  
            16                   NaN  
        
        """
        if timeseries_metadata is None:
            timeseries_metadata = self.fetch_locations_timeseries_metadata(
                locids=[locid], **kwargs
            )
        timeseries_metadata["param_label"] = (
            timeseries_metadata.param + "." + timeseries_metadata.label
        )
        remap_ts_uids = (
            timeseries_metadata.loc[:, ["ts_uid", "param_label"]]
            .set_index("ts_uid")
            .param_label
        )
        df = pd.concat(
            [
                self.fetch_timeseries_relatives(ts_uid)
                for ts_uid in timeseries_metadata.ts_uid.unique()
            ]
        )
        if ts_id_type in ("both", "param_label"):
            for ts_uid_col in ("queried_ts_uid", "input_ts_uid", "output_ts_uid"):
                new_col = ts_uid_col.replace("_uid", "_param_label")
                col_idx = list(df.columns).index(ts_uid_col)
                df.insert(col_idx + 1, new_col, df[ts_uid_col].map(remap_ts_uids))
                if ts_id_type == "param_label":
                    df = df.drop(ts_uid_col, axis=1)
        elif ts_id_type == "uid":
            pass
        else:
            raise KeyError(
                "TimeSeries ID type must be either 'param_label', 'uid', or 'both'"
            )
        df = df.drop_duplicates([c for c in df.columns if not "queried_ts" in c])
        if not include_queried_ts_info:
            drop_cols = [c for c in df.columns if "queried_ts" in c]
            df = df.drop(drop_cols, axis=1)

        remap_types = {pt: pt for pt in df.processor_type.unique()}
        remap_types.update(
            {
                "fillmissingdata": "fill missing data",
                "correctedpassthrough": "corr. pass through",
                "datumconversion": "datum conversion",
                "ratingmodel": "rating model",
            }
        )
        df["processor_type"] = df.processor_type.map(remap_types)
        return df.reset_index(drop=True)

    def fetch_timeseries_points_only(self, ts_uid, start=None, finish=None):
        """Fetch all timeseries data points.

        Args:
            ts_uid (str): timeseries unique ID

        Returns:
            pandas.DataFrame with columns "timestamp" (pd.Timestamp)
            and "value" (numeric)

        This does not provide any work-around to the "maximum number of points"
        limitation of AQTS.

        """
        params = {
            "TimeSeriesUniqueId": ts_uid,
            "GetParts": "PointsOnly",
        }
        if start:
            params["QueryFrom"] = format_iso8601(start)
        if finish:
            params["QueryTo"] = format_iso8601(finish)

        response = self.ts.publish.get("GetTimeSeriesCorrectedData", params=params)
        df = pd.json_normalize(response.json()["Points"])
        if len(df.columns) == 0:
            return pd.DataFrame(columns=["timestamp", "value"])
        else:
            df["Timestamp"] = convert_timestamps(df["Timestamp"])
            df = df.rename(columns={"Timestamp": "timestamp", "Value.Numeric": "value"})
            return df

    def fetch_timeseries_metadata_only(self, ts_uid, start=None, finish=None):
        """Fetch metadata for a timeseries.

        Args:
            ts_uid (str): timeseries unique ID

        Returns:
            dictionary with keys "min_dt" (earliest timestamp of data),
            "max_dt" (latest), "ts_uid" (timeseries unique ID),
            "locid" (location identifier), "label" (timeseries label),
            "param" (timeseries parameter), and "unit" (timeseries unit).
            Also "dts" which is a dictionary of pandas.DataFrames for the
            different metadata fields: "grades", "quals", "interp_types",
            "gap_tols", and "approvals".

        """
        params = {
            "TimeSeriesUniqueId": ts_uid,
            "GetParts": "MetadataOnly",
        }
        if start:
            params["QueryFrom"] = format_iso8601(start)
        if finish:
            params["QueryTo"] = format_iso8601(finish)

        response = self.ts.publish.get("GetTimeSeriesCorrectedData", params=params)

        key_mapping = {
            "grades": "Grades",
            "approvals": "Approvals",
            "quals": "Qualifiers",
            "gap_tols": "GapTolerances",
            "interp_types": "InterpolationTypes",
        }
        dfs = {k: pd.json_normalize(response.json()[v]) for k, v in key_mapping.items()}
        for k, df in dfs.items():
            for col in ["StartTime", "EndTime"]:
                if not col in dfs[k]:
                    dfs[k][col] = pd.Series([], dtype=str)
                dfs[k][col] = pd.to_datetime(
                    convert_timestamps(dfs[k][col]), errors="coerce"
                )
            if "GradeCode" in df:
                dfs[k]["GradeCode"] = pd.to_numeric(dfs[k]["GradeCode"])

        min_all_dt = None
        max_all_dt = None
        for key, df in dfs.items():
            dt_values = [v for v in df["StartTime"].unique() if not pd.isnull(v)]
            dt_values += [v for v in df["EndTime"].unique() if not pd.isnull(v)]
            if len(dt_values):
                min_dt = min(dt_values)
                max_dt = max(dt_values)
                if min_all_dt is None or min_all_dt > min_dt:
                    min_all_dt = min_dt
                if max_all_dt is None or max_all_dt < max_dt:
                    max_all_dt = max_dt

        return_data = {
            "min_dt": min_all_dt,
            "max_dt": max_all_dt,
        }
        meta_keys = {
            "UniqueId": "ts_uid",
            "Parameter": "param",
            "Label": "label",
            "LocationIdentifier": "locid",
            "Unit": "unit",
        }
        for key, value in response.json().items():
            if key in meta_keys:
                return_data[meta_keys.get(key)] = value
        return_data["dfs"] = dfs

        return return_data

    def fetch_timeseries_data(
        self,
        locid=None,
        param="Depth to Water",
        label="Best Available",
        ts_uid=None,
        label_startswith=True,
        start=None,
        finish=None,
        freq="as-recorded",
        max_gap_days=1,
        keep_grades=(1, 20, 30),
        **kwargs,
    ):
        """Fetch all timeseries data and add metadata.

        Args:
            locid (str, optional): location identifier
            param (str, optional): parameter, default "Depth to Water". Substitutes
                for groundwater parameters will work e.g. "dtw", "swl", "rswl", "ec",
                "tds".
            label (str, optional): label, default "Best Available"
            ts_uid (str, optional): timeseries unique ID. If supplied,
                it will be used and the other arguments above will be
                ignored. If not supplied, some combination of the
                arguments above, sufficient to identify a single
                timeseries, will be used.
            label_startswith (bool): if True, and if the argument
                *label* above is used to identify a timeseries, the
                available timeseries will be filtered using
                ``label.str.startswith()`` instead of ``label ==``,
                such that for example ``label="Best Available"``
                will match the value "Best Available--Continuous".
                If False, an exact match will be used.
            start (pd.Timestamp in ACST): first time to retrieve data from
                e.g. to provide 9am on the 17th May 2023,
                use ``start=gd.timestamp_acst("2023-05-17 09:00")``
            finish (pd.Timestamp in ACST): last time to retrieve data from.
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

        This does not provide any work-around to the "maximum number of points"
        limitation of AQTS.

        It fails if more than one dataset/timeseries is identified in AQTS.

        """
        param_subs = PARAM_SUBS_SAGD_TO_AQ
        if param in param_subs:
            param = param_subs[param]

        if ts_uid is None:
            loc_ts = self.fetch_locations_timeseries_metadata([locid], from_cache=False)
            if len(loc_ts) == 0:
                return []
            elif len(loc_ts) == 1:
                ts_uid = loc_ts.ts_uid.iloc[0]
            else:
                if not param is None:
                    loc_ts = loc_ts[loc_ts.param == param]
                if not label is None:
                    if label_startswith:
                        loc_ts = loc_ts[loc_ts.label.str.startswith(label)]
                    else:
                        loc_ts = loc_ts[loc_ts.label == label]
                if len(loc_ts) == 1:
                    ts_uid = loc_ts.ts_uid.iloc[0]
                elif len(loc_ts) > 1:
                    raise KeyError(
                        f"More than one timeseries has been identified. "
                        "Please specify which time series to download."
                    )
                elif len(loc_ts) == 0:
                    raise KeyError(f"No timeseries were identified. ")
        meta = self.fetch_timeseries_metadata_only(ts_uid, start=start, finish=finish)
        pts = self.fetch_timeseries_points_only(ts_uid, start=start, finish=finish)
        logger.debug(f"len(pts)={len(pts)}")
        if len(pts) == 0:
            if "param" in meta:
                return pd.DataFrame(
                    columns=[
                        "timestamp",
                        meta["param"],
                        "grade",
                        "approval",
                        "qualifier",
                    ]
                )
            else:
                return []
        else:
            if "param" in meta:
                pts = pts.rename(columns={"value": meta["param"]})
                logger.debug(f"renamed 'value' to meta['param']={meta['param']}")

            pts = apply_time_periods(
                meta["dfs"]["grades"],
                "GradeCode",
                pts,
                "timestamp",
                target_apply_as="grade",
            )
            pts = apply_time_periods(
                meta["dfs"]["approvals"],
                "LevelDescription",
                pts,
                "timestamp",
                target_apply_as="approval",
            )
            pts = apply_time_periods(
                meta["dfs"]["quals"],
                "Identifier",
                pts,
                "timestamp",
                target_apply_as="qualifier",
            )

            for col in ["qualifier", "approval"]:
                if not col in pts:
                    pts[col] = ""

            ret_val = pts
        logger.debug(f"len(ret_val)={len(ret_val)}")
        dfs = normalise_and_clean_logger_data(ret_val.set_index("timestamp"))
        logger.debug(
            f"[len(df) for df in dfs]=" + ",".join([str(len(df)) for df in dfs])
        )
        dfs = resample_logger_data(
            dfs, freq=freq, max_gap_days=max_gap_days, keep_grades=keep_grades
        )
        logger.debug(
            f"[len(df) for df in dfs]=" + ",".join([str(len(df)) for df in dfs])
        )
        return dfs


def convert_timestamps(values, utc_is_null=True):
    """Convert AQTS timestamp to datetime.

    Args:
        values (sequence of str): formats are e.g.
            "2021-09-05T12:00:05.000000+09:30"
        utc_is_null (bool): weird quirk - AQTS gives the
            "start of time" value and "end of time"
            values (years 0000 and 9999) the UTC
            timezone which makes for confusion later on.
            If True, convert any values in UTC to
            ``pd.NaT``.

    Also deals with the fact AQTS actually uses - :-( -
    the ISO8601-compliant "24:00:00", which Python
    doesn't understand.

    Returns:
        list of tz-aware datetime objects.

    """
    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})\.\d*([-+]{1}\d{2}):(\d{2})"
    )
    format_str = "%Y-%m-%d %H:%M:%S %z"

    converted_values = []
    for value in values:
        match = pattern.match(value)
        date_match = match.group(1)
        time_match = match.group(2)
        if match.group(2) == "24:00:00":
            date = datetime.date.fromisoformat(match.group(1))
            date += datetime.timedelta(days=1)
            date_match = date.strftime("%Y-%m-%d")
            time_match = "00:00:00"
        timestamp = (
            date_match + " " + time_match + " " + match.group(3) + match.group(4)
        )
        tzone = match.group(3) + match.group(4)
        if tzone[1:] == "0000" and utc_is_null:
            converted_values.append(pd.NaT)
        else:
            dt = datetime.datetime.strptime(timestamp, format_str)
            converted_values.append(dt)
    return converted_values


def apply_time_periods(
    periods,
    period_apply_col,
    target_df,
    target_dt_col,
    target_apply_as=None,
    period_dt_cols=("StartTime", "EndTime"),
):
    """Apply metadata stored as time periods to the timeseries dataframe itself.

    Args:
        periods (pd.DataFrame): metadata periods
        period_apply_col (str): apply the value from this column
        target_df (pd.DataFrame): timeseries data
        target_dt_col (str): column in ``target_df`` which contains the timestamp
        target_apply_as (str): name of the column in ``target_df`` to populate
            with the values from "period_apply_col". If None, the value of
            "period_apply_col" will be used.
        period_dt_cols (tuple): the name of the columns in ``periods`` which
            store the start and end time of the period.

    Returns:
        a copy of ``target_df`` with ``target_apply_as`` added as a new
        column.

    You're unlikely to need to use this function.

    """
    target = target_df.copy()
    if target_apply_as is None:
        target_apply_as = period_apply_col
    for idx, record in (
        periods.rename(
            columns={
                period_apply_col: "value",
                period_dt_cols[0]: "from_dt",
                period_dt_cols[1]: "to_dt",
            }
        )
        .assign(value_name=target_apply_as)
        .iterrows()
    ):
        if pd.isnull(record.from_dt) and pd.isnull(record.to_dt):
            target[record.value_name] = record["value"]
        elif pd.isnull(record.from_dt):
            target.loc[target[target_dt_col] < record.to_dt, record.value_name] = (
                record["value"]
            )
        elif pd.isnull(record.to_dt):
            target.loc[target[target_dt_col] >= record.from_dt, record.value_name] = (
                record["value"]
            )
        else:
            target.loc[
                (target[target_dt_col] >= record.from_dt)
                & (target[target_dt_col] < record.to_dt),
                record.value_name,
            ] = record["value"]
    return target


def convert_timeseries_relationships_to_graphs(df):
    """Convert relationships between timeseries to a graph.

    Args:
        df (pd.DataFrame): see :meth:`dew_gwdata.DEWAquarius.fetch_timeseries_relationships_for_location`

    Returns: list of nx.DiGraph objects for each set of connected timeseries
        in this location.

    """
    nodes = np.hstack(
        [df.input_ts_param_label.unique(), df.output_ts_param_label.unique()]
    )
    edges = df[["input_ts_param_label", "output_ts_param_label"]].to_records(
        index=False
    )
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for idx, row in df.iterrows():
        graph.add_edge(row.input_ts_param_label, row.output_ts_param_label)

    graphs = []
    for subgraph_nodes in nx.connected_components(graph):
        subgraph = nx.DiGraph()
        subgraph.add_nodes_from(subgraph_nodes)
        for i, (node_from, node_to) in enumerate(edges):
            if node_from in subgraph_nodes:
                subgraph.add_edge(
                    node_from,
                    node_to,
                    **{k.replace(".", "_"): v for k, v in df.iloc[i].to_dict().items()},
                )  # processor_type=df.iloc[i].processor_type)
        graphs.append(subgraph)

    return graphs


def draw_timeseries_relationship_graph(
    graph, edge_field="processor_type", edge_break_on_whitespace=True, ax=None
):
    """Draw a representation of how timeseries relate to one another in terms of processor types.

    Args:
        graph (networkx.DiGraph): see :meth:`dew_gwdata.DEWAquarius.convert_timeseries_relationships_to_graphs`
        edge_field (str): field to use for the edge label
        edge_break_on_whitespace (bool)
        ax (matplotlib.Axes): optional. It's best to let this function size the figure automatically.

    Returns: matplotlib Axes

    Note this was not tested on processors with multiple processing periods.

    """
    import matplotlib.pyplot as plt

    def get_edge_label(node_from, node_to):
        for n_from, n_to, data in graph.edges.data():
            if n_from == node_from and n_to == node_to:
                return data[edge_field]

    if ax is None:
        fig_height = len(graph.nodes) * 1.35
        fig = plt.figure(figsize=(10, fig_height))
        ax = fig.add_subplot(111)

    squash_node_label = lambda n: str(n).replace(".", ".\n", 1).replace("--", "--\n")
    if edge_break_on_whitespace:
        reformat_edge_label = lambda e: str(e).replace("nan", "").replace(" ", "\n")
    else:
        reformat_edge_label = lambda e: str(e).replace("nan", "")
    edge_labels = {
        (squash_node_label(n_from), squash_node_label(n_to)): reformat_edge_label(
            get_edge_label(n_from, n_to)
        )
        for n_from, n_to in graph.edges
    }

    graph = nx.relabel_nodes(
        graph, {n: squash_node_label(n) for n in graph.nodes}, copy=True
    )

    pos = nx.planar_layout(
        graph,
    )

    node_size = 2000
    nx.draw_networkx_nodes(
        graph,
        ax=ax,
        pos=pos,
        node_size=node_size,
        alpha=0.2,
        linewidths=0,
        node_color="tab:blue",
    )
    nx.draw_networkx_labels(
        graph,
        ax=ax,
        pos=pos,
        font_size=6,
        bbox=dict(facecolor="w", alpha=0.8, edgecolor="tab:blue", lw=0.5),
    )
    nx.draw_networkx_edges(
        graph,
        ax=ax,
        pos=pos,
        width=0.8,
        arrowstyle="-|>",
        arrowsize=20,
        node_size=node_size * 1.1,
    )
    nx.draw_networkx_edge_labels(
        graph,
        ax=ax,
        pos=pos,
        edge_labels=edge_labels,
        font_size=6,
    )
    return ax


def unstack_aq_tags(df, tag_col="tags", pair_sep="|", key_value_sep=":"):
    """Unstack a pandas DataFrame containing concatenated tag key:value pairs.

    Args:
        df (pandas.DataFrame): input table
        tag_col (str): column containing concatenated key:value pairs
        pair_sep (str): character separating key:value pairs
        key_value_sep (str): character separating key and value

    Returns: pandas.DataFrame with *tag_col* column removed replaced by *tag_combined*
        *tag_key*, *tag_value*, with a row per tag key:value pair.

    """
    tagdf = (
        df.set_index(df.columns.drop(tag_col).tolist())
        .tags.str.split(pair_sep, expand=True)
        .stack()
        .reset_index()
        .rename(columns={0: tag_col})
        .loc[:, df.columns]
    )
    tagdf = tagdf.rename(columns={"tags": "tag_combined"})
    tagdf["tag_key"] = [
        t[0] if len(t) else "" for t in tagdf.tag_combined.str.split(key_value_sep)
    ]
    tagdf["tag_value"] = [
        t[-1] if len(t) else "" for t in tagdf.tag_combined.str.rsplit(key_value_sep)
    ]
    return tagdf


def get_swims_metadata_connection():
    conn = pyodbc.connect(
        "Driver={SQL Server};"
        "Server=sql2019-prod.env.sa.gov.au;"
        "Database=SWIMS_Metadata;"
        "Trusted_Connection=yes;"
    )
    return conn


class SWIMSMetadata(SQLServerDb):
    API_ENDPOINT_NAME = "query_swims_metadata"

    def __init__(self, *args, sagd_conn=None, **kwargs):
        super(SWIMSMetadata, self).__init__(*args, **kwargs)
        if sagd_conn is None:
            from .sageodata_database import connect

            self.sagd_conn = connect()
        else:
            self.sagd_conn = sagd_conn

    def connect(self):
        self.conn = get_swims_metadata_connection()

    def run_query_for_drillholes(self, sql, dh_nos):
        logger.debug(f"Finding unit_hyphens for dh_nos={dh_nos}")
        wells = self.sagd_conn.wells_summary(dh_nos)
        unit_hyphens = list(wells.unit_hyphen.unique())
        dfs = []
        query = SQL(sql, unit_hyphen=unit_hyphens)
        query.chunksize = 1000
        for subquery in query:
            dfs.append(self.query(subquery))
        return pd.concat(dfs)

    def datasets(self, dh_nos, add_well_ids=True, **kwargs):
        sql = """
        select  Id as id,
                LocationId as locid,
                LocationName as loc_name,
                LocationType as loc_type,
                TimeSeriesIdentifier as tsid,
                Label as label,
                LabelFirstPart as label_first_part,
                TimeSeriesType as ts_type,
                "Parameter" as aq_param,
                Unit as unit,
                InterpolationType as interpolation_type,
                UtcOffset as utc_offset,
                FirstDataPointValue as first_data_value,
                FirstDataPointDateTime as first_data_timestamp,
                FirstDataPointGrade as first_data_grade,
                LastDataPointValue as last_data_value,
                LastDataPointDateTime as last_data_timestamp,
                LastDataPointGrade as last_data_grade,
                "Comment" as "comment",
                Description as descr,
                Publish as publish,
                Latitude as lat,
                Longitude as lon,
                TimeSeriesUniqueId as ts_uid,
                LocationUniqueId as loc_uid
        from SWIMS_Metadata.dbo.DataSets
        where LocationId in {UNIT_HYPHEN}
        """
        wells = self.sagd_conn.wells_summary(dh_nos)
        df = self.run_query_for_drillholes(sql, dh_nos)
        df["sagd_param"] = df.aq_param.map(PARAM_SUBS_AQ_TO_SAGD)
        id_cols = ["dh_no", "unit_hyphen", "obs_no", "dh_name"]
        fdf = pd.merge(
            df, wells[id_cols], left_on="locid", right_on="unit_hyphen", how="left"
        )
        cols = [c for c in fdf.columns if not c in id_cols]
        return fdf[id_cols + cols]
