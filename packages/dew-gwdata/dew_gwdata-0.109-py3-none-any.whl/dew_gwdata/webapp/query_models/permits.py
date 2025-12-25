import logging

import pandas as pd
from pydantic import BaseModel

from dew_gwdata import sageodata as connect_to_sageodata


logger = logging.getLogger(__name__)


class Permits(BaseModel):
    env: str = "PROD"

    # Group 1 - search by permit number range
    permit_no_from: int = 0
    permit_no_to: int = 0

    # Group 2 - search by permit number
    permit_no: int = 0

    # Group 3 - search by issue date range.
    issue_date_from: str = ""
    issue_date_to: str = ""

    holder_name: str = ""

    def find_permits(self):
        db = connect_to_sageodata(service_name=self.env)

        permits = None

        if self.permit_no_from or self.permit_no_to:
            logger.debug(
                f"Searching for permits between query.permit_no_from = {self.permit_no_from} and query.permit_no_to = {self.permit_no_to}"
            )
            if not self.permit_no_from:
                permit_no_from = 0
            else:
                permit_no_from = self.permit_no_from
            if not self.permit_no_to:
                permit_no_to = 10000000
            else:
                permit_no_to = self.permit_no_to
            df = db.permit_details_for_permit_no_range(permit_no_from, permit_no_to)
            title = (
                f"Permit numbers between {self.permit_no_from} and {self.permit_no_to}"
            )
            query_params = [
                f"permit_no_from={self.permit_no_from}",
                f"permit_no_to={self.permit_no_to}",
            ]
        elif self.permit_no:
            logger.debug(f"Searching for permit number {self.permit_no}")
            df = db.permit_details([self.permit_no])
            title = f"Permit number {self.permit_no}"
            query_params = [f"permit_no={self.permit_no}"]
        elif self.issue_date_from or self.issue_date_to:
            logger.debug(
                f"Searching for permits issued between {self.issue_date_from} and {self.issue_date_to}"
            )
            issue_date_from = pd.Timestamp("0001-01-01")
            issue_date_to = pd.Timestamp("9999-12-31")
            if self.issue_date_from:
                issue_date_from = pd.Timestamp(self.issue_date_from)
            if self.issue_date_to:
                issue_date_to = pd.Timestamp(self.issue_date_to)
            df = db.permit_details_between_dates(
                issue_date_from.strftime("%Y-%m-%d %H:%M:%S"),
                issue_date_to.strftime("%Y-%m-%d %H:%M:%S"),
            )
            title = f"Permits issued between {self.issue_date_from} and {self.issue_date_to}"
            query_params = [
                f"issue_date_from={self.issue_date_from}",
                f"issue_date_to={self.issue_date_to}",
            ]
        elif self.holder_name:
            logger.debug(f"Searching for permits with holder_name {self.holder_name}")
            df = db.query(
                f"select permit_no from wp_permit_wls_vw where holder_name like '{self.holder_name.upper()}'"
            )
            if len(df):
                df = db.permit_details(df.permit_no)
            else:
                df = db.permit_details([])
            title = f"Permits matching '{self.holder_name}'"
            query_params = [
                f"holder_name={self.holder_name}",
            ]
        else:
            logger.debug(f"Empty search for permits.")
            df = db.permit_details([])
            title = f"Empty search"
            query_params = []

        return df, title, "&".join(query_params)
