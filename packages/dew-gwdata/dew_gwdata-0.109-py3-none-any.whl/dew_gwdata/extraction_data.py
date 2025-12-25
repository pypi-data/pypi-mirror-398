import pandas as pd

from .package_database import connect_to_package_database
from .utils import SQL


class ExtractionInjectionDatabase:
    def __init__(self, pkg_db=None, sagd_db=None, sagd_env="prod"):
        if pkg_db is None:
            self.pkg_db = connect_to_package_database()
        else:
            self.pkg_db = pkg_db

        if sagd_db is None:
            from dew_gwdata.sageodata_database import connect

            self.sagd_db = connect(service_name=sagd_env)
        else:
            self.sagd_db = sagd_db

    def query(self, sql, **kwargs):
        dfs = []
        query = SQL(sql, **kwargs)
        query.chunksize = 1000
        for subquery in query:
            dfs.append(pd.read_sql(subquery, self.pkg_db))
        return pd.concat(dfs)

    def query_usage_for_drillholes(self, dh_nos):
        sql = """select * from usage
        where unit_hyphen in {UNIT_HYPHEN}
        and month is null
        """
        dh_df = self.sagd_db.drillhole_details(dh_nos)
        unit_hyphens = dh_df.dropna(subset=["unit_hyphen"]).unit_hyphen.unique()
        return self.query(sql, unit_hyphen=unit_hyphens)
