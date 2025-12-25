import logging

import pyodbc

from .utils import *
from .webapp.config import WEB_APP_HOST, WEB_APP_PORT

logger = logging.getLogger(__name__)


def get_wde_connection():
    conn = pyodbc.connect(
        "Driver={SQL Server};"
        "Server=sql2012-prod.env.sa.gov.au;"
        "Database=WDE_Extended;"
        "Trusted_Connection=yes;"
    )
    return conn


class WDEExtended(SQLServerDb):
    API_ENDPOINT_NAME = "query_wde_extended"

    def connect(self):
        self.conn = get_wde_connection()

    def logger_installations(self, dh_nos, add_well_ids=True, **kwargs):
        sql = """SELECT DRILLHOLE_NO AS dh_no,
            DATE_INSTALLED as install_date,
            TYPE as "type",
            MODEL as model,
            SERIAL_NO as serial_no,
            TELEMETRY as telemetry,
            Tolerance as tolerance_cm,
            Active as active,
            COMMENT as comments
        FROM   WDE_Extended.dbo.Logger
        WHERE  DRILLHOLE_NO IN {DH_NO}"""
        df = self.run_query_for_drillholes(sql, dh_nos)
        if add_well_ids and len(df):
            df = add_well_ids_to_query_result(df, **kwargs)
        return df

    def logger_readings(self, dh_nos, add_well_ids=True, **kwargs):
        sql = """SELECT DRILLHOLE_NO AS dh_no,
            READING_DATE AS reading_date,
            DEPTH_TO_WATER as dtw,
            PRESSURE AS pressure,
            TEMPERATURE as "temp",
            BATTERY_PERCENTAGE AS battery_pct,
            MEMORY_PERCENTAGE AS memory_pct,
            COMMENT AS comments,
            CreatedBy AS read_by
        FROM   WDE_Extended.dbo.Logger_Data
        WHERE  DRILLHOLE_NO IN {DH_NO}"""
        df = self.run_query_for_drillholes(sql, dh_nos)
        if add_well_ids and len(df):
            df = add_well_ids_to_query_result(df, **kwargs)
        return df

    def maintenance_issues(self, dh_nos, add_well_ids=True, **kwargs):
        sql = """SELECT drillHoleNo  AS dh_no, 
            DateReported AS reported_date,
            ReportedBy AS reported_by,
            Priority AS priority,
            MTCRequired AS comments,
            DateCompleted AS completed_date,
            ActionedBy AS actioned_by,
            ActionDetails AS action_comments,
            OtherAction AS action_other
        FROM   WDE_Extended.dbo.WellMaintenanceNotes 
        WHERE  drillHoleNo IN {DH_NO}"""
        df = self.run_query_for_drillholes(sql, dh_nos)
        if add_well_ids and len(df):
            df = add_well_ids_to_query_result(df, **kwargs)
        return df

    def wde_alerts(self, dh_nos, add_well_ids=True, **kwargs):
        sql = """SELECT DrillholeNo AS dh_no,
            DateCreated AS creation_date,
            Active AS active,
            Description AS description,
            CreatedBy AS created_by,
            ModifiedBy AS modified_by,
            DateModified AS modified_date
        FROM   WDE_Extended.dbo.Alerts
        WHERE  DrillholeNo IN {DH_NO}"""
        df = self.run_query_for_drillholes(sql, dh_nos)
        if add_well_ids and len(df):
            df = add_well_ids_to_query_result(df, **kwargs)
        return df
