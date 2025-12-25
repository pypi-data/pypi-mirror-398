import logging

import pandas as pd
from pydantic import BaseModel

from dew_gwdata import sageodata as connect_to_sageodata
from dew_gwdata.webapp import utils as webapp_utils


logger = logging.getLogger(__name__)


class GeophysLogJobs(BaseModel):
    env: str = "PROD"

    # SEARCH FOR WELLS - GROUPED EXCLUSIVELY
    # --------------------------------------

    # Group 1 - search by job number range
    job_no_from: int = 0
    job_no_to: int = 0

    # Group 2 - search by job number
    job_no: int = 0

    # Group 3 - search by discrete job numbers
    jobstr: str = ""

    # Group 4 - search by logged date range
    logged_date_from: str = ""
    logged_date_to: str = ""

    # Group 5 - location search
    location: str = ""

    # FILTER OPTIONS - reduce list of wells through filter options
    # ------------------------------------------------------------

    location_contains: str = ""
    purpose_contains: str = ""
    operator_contains: str = ""
    vehicle_contains: str = ""
    log_depth_min: float = 0

    # SORT OPTIONS
    # ------------

    sort: str = "logged_date"
    order: str = "ascending"

    def find_jobs(self):
        db = connect_to_sageodata(service_name=self.env)

        # SEARCH FOR JOBS
        # ----------------
        wells = None

        # Group 1 - search by job number range
        if self.job_no_from or self.job_no_to:
            if not self.job_no_from:
                self.job_no_from = 0
            if not self.job_no_to:
                self.job_no_to = 100000
            df = db.geophys_log_metadata_by_job_no_range(
                self.job_no_from, self.job_no_to
            )
            title = f"Jobs between {self.job_no_from} and {self.job_no_to}"
            query_params = [
                f"job_no_from={self.job_no_from}",
                f"job_no_to={self.job_no_to}",
            ]

        # Group 2 - search by job number
        elif self.job_no:
            df = db.geophys_log_metadata_by_job_no([self.job_no])
            title = f"Job number {self.job_no}"
            query_params = [f"job_no={self.job_no}"]

        elif self.jobstr:
            job_nos = webapp_utils.urlstr_to_dhnos(self.jobstr)
            df = db.geophys_log_metadata_by_job_no(job_nos)
            title = f"Job number selection"
            query_params = [f"jobstr={self.jobstr}"]

        # Group 4 - search by logged date range
        elif self.logged_date_from or self.logged_date_to:
            if not self.logged_date_from:
                self.logged_date_from = "1950-01-01"
            if not self.logged_date_to:
                self.logged_date_to = "2100-01-01"
            logged_date_from = pd.Timestamp(self.logged_date_from)
            logged_date_to = pd.Timestamp(self.logged_date_to)
            df = db.geophys_log_metadata_by_logged_date_range(
                logged_date_from, logged_date_to
            )
            title = f"Jobs logged between {logged_date_from.strftime('%d/%m/%Y')} and {logged_date_to.strftime('%d/%m/%Y')}"
            query_params = [
                f"logged_date_from={self.logged_date_from}",
                f"logged_date_to={self.logged_date_to}",
            ]

        # Group 5 - location search
        elif self.location:
            df = db.geophys_log_metadata_by_location(self.location)
            title = f"Jobs logged at location '{self.location}'"
            query_params = [f"location={self.location}"]

        else:
            df = db.geophys_log_metadata_by_job_no([])
            title = f"Empty search"
            query_params = [
                f"job_no=0",
            ]

        # FILTER
        # ------

        if len(df):
            if self.location_contains:
                df = df[
                    df.location.str.contains(
                        self.location_contains, regex=False, na=False, case=False
                    )
                ]
                query_params.append(f"location_contains={self.location_contains}")

            if self.purpose_contains:
                df = df[
                    df.purpose.str.contains(
                        self.purpose_contains, regex=False, na=False, case=False
                    )
                ]
                query_params.append(f"purpose_contains={self.purpose_contains}")

            if self.operator_contains:
                df = df[
                    df.operators.str.contains(
                        self.operator_contains, regex=False, na=False, case=False
                    )
                ]
                query_params.append(f"operator_contains={self.operator_contains}")

            if self.vehicle_contains:
                df = df[
                    df.vehicle.str.contains(
                        self.vehicle_contains, regex=False, na=False, case=False
                    )
                ]
                query_params.append(f"vehicle_contains={self.vehicle_contains}")

            if self.log_depth_min:
                df = df[(df.max_log_depth >= self.log_depth_min)]
                query_params.append(f"log_depth_min={self.log_depth_min}")

        # SORT
        # ----

        if self.sort == "dh_no":
            query_params.append("sort=dh_no")
        elif self.sort == "unit_hyphen":
            query_params.append("sort=unit_hyphen")
        elif self.sort == "obs_no":
            query_params.append("sort=obs_no")
        elif self.sort == "logged_date":
            query_params.append("sort=logged_date")
        elif self.sort == "job_no":
            query_params.append("sort=job_no")

        query_params.append(f"order={self.order}")

        return df, title, "&".join(query_params)
