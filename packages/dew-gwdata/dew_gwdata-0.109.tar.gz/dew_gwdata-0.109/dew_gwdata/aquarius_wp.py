import aquarius_webportal

from .gwdata import normalise_and_clean_logger_data, resample_logger_data


def connect_to_aqwp(env="prod"):
    """Connect to AQ Web Portal

    Args:
        env (str): either "prod", "test", or "dev"

    Returns:
        aquarius_webportal.AquariusWebPortal object: ready for use!

    """
    return DEWAquariusWebPortal(env=env)


def resolve_param_name(param):
    if param == "dtw":
        param = "Depth to Water"
    elif param == "swl":
        param = "SWL"
    elif param == "rswl":
        param = "RSWL"
    elif param == "ec":
        param = "EC Corr"
    elif param == "tds":
        param = "TDS from EC"
    elif param == "rainfall":
        param = "Rainfall"
    else:
        raise KeyError(f"param {repr(param)} not known")
    return param


class DEWAquariusWebPortal:
    def __init__(self, server=None, env="prod"):
        if server is None:
            if env.lower().startswith("prod"):
                server = "https://water.data.sa.gov.au"
            elif env.lower().startswith("qa") or env.lower().startswith("test"):
                server = "https://envswimsq02.env.sa.gov.au"
            elif env.lower().startswith("dev"):
                server = "https://envswimsd02.env.sa.gov.au"
        self.portal = aquarius_webportal.AquariusWebPortal(server)

    def find_logger_datasets(self, unit_hyphen, param="swl"):
        """Obtain groundwater logger datasets.

        Args:
            unit_hyphen (str): unit number in hyphenated form e.g. '7025-808'
            param (str): either "dtw", "swl", "rswl", "ec", "tds", "rainfall"
            resample_freq (str): a pandas re-sampling frequency or None for
                the raw data.

        """
        param = resolve_param_name(param)

        dsets = self.portal.fetch_datasets(param_name=param)
        dsets = dsets[dsets.loc_id == unit_hyphen]
        dsets = dsets[dsets.label != "Field Visits"]

        return dsets

    def get_best_available_logger_dataset(self, unit_hyphen, param="swl", **kwargs):
        """Return best available dataset for well.

        unit_hyphen (str): groundwater location in AQWP
        param (str): "dtw", "swl", "rswl", "ec", "tds", or "rainfall"
        freq (str): either "as-recorded" (data points as they exist) or a pandas
            frequency string e.g "6H", "2d" etc.
        max_gap_days (float): maximum allowable gap between data points in days
        keep_grades (tuple): grades to keep. 1 = telemetry, 10 = water level outside
            of recordable range, 15 = poor which GW Team uses to mean "unusable",
            20 = fair, 30 = good. Use None to keep all measurements.
        extra_data_types (str/sequence): The additional metadata fields
            to retrieve for each data point - either "all", None, or
            a sequence of strings with one or more of "grade", "approval", "qualifier",
            and "interpolation_type". None is the default
        start (pd.Timestamp): earliest data to retrieve - None by default
        finish (pd.Timestamp): latest data to retrieve - None by default

        Returns:
            list of pd.DataFrame: each df is guaranteed to have no gaps in the
            timestamp column > max_gap_days. The columns of each dataframe are:

                - "timestamp": pd.Timestamp - tz-aware with timezone UTC+09:30 i.e. ACST
                - the parameter, titled either "dtw", "swl", "rswl", "ec", "tds", or "rainfall"
                - "chunk_id" - this integer increments from 0, 1, 2 depending on how
                    many gaps were found in the data (gaps > max_gap_days above)

        """
        dsets = self.find_logger_datasets(unit_hyphen, param)
        for idx, dset in dsets.iterrows():
            if "Best Available" in dset.label:
                return self.get_logger_dataset(dset.dset_name, **kwargs)
        return []

    def get_logger_dataset(
        self,
        dset_name,
        freq="as-recorded",
        max_gap_days=1,
        keep_grades=(1, 20, 30),
        extra_data_types=None,
        start=None,
        finish=None,
    ):
        """Download logger dataset from AQ WP.

        Args:
            dset_name (str): e.g. param.label@location
            freq (str): either "as-recorded" (data points as they exist) or a pandas
                frequency string e.g "6H", "2d" etc.
            max_gap_days (float): maximum allowable gap between data points in days
            keep_grades (tuple): grades to keep. 1 = telemetry, 10 = water level outside
                of recordable range, 15 = poor which GW Team uses to mean "unusable",
                20 = fair, 30 = good. Use None to keep all measurements.
            extra_data_types (str/sequence): The additional metadata fields
                to retrieve for each data point - either "all", None, or
                a sequence of strings with one or more of "grade", "approval", "qualifier",
                and "interpolation_type". ["grade"] is the default.
            start (pd.Timestamp): earliest data to retrieve - None by default
            finish (pd.Timestamp): latest data to retrieve - None by default

        Returns:
            list of pd.DataFrame: each df is guaranteed to have no gaps in the
            timestamp column > max_gap_days. The columns of each dataframe are:

                - "timestamp": pd.Timestamp - tz-aware with timezone UTC+09:30 i.e. ACST
                - the parameter, titled either "dtw", "swl", "rswl", "ec", "tds" or "rainfall"
                - "chunk_id" - this integer increments from 0, 1, 2 depending on how
                  many gaps were found in the data (gaps > max_gap_days above)

        """
        if extra_data_types:
            assert list(sorted(extra_data_types)) in (
                ["grade"],
                ["approval"],
                ["approval", "grade"],
            )
        df = self.portal.fetch_dataset(
            dset_name, extra_data_types=extra_data_types, start=start, finish=finish
        )

        df = normalise_and_clean_logger_data(df)

        return resample_logger_data(
            df, freq=freq, max_gap_days=max_gap_days, keep_grades=keep_grades
        )
