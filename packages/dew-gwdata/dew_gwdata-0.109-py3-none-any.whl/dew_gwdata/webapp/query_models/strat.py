from datetime import datetime
from typing import Annotated
import logging
import fnmatch
import pprint

import pandas as pd
import ausweather
from fastapi import Query
from pydantic import BaseModel

from dew_gwdata import sageodata as connect_to_sageodata
from dew_gwdata.webapp import utils as webapp_utils


logger = logging.getLogger(__name__)


class StratUnits(BaseModel):
    env: str = "PROD"

    map_symbol: str = ""
    strat_name: str = "%"

    def find_strat_units(self):
        db = connect_to_sageodata(service_name=self.env)
        df = db.query(
            f"select strat_unit_no from st_strat_unit "
            f"where map_symbol like '{self.map_symbol}' "
            f"and upper(strat_name) like upper('{self.strat_name}')"
        )
        return list(df.strat_unit_no.values)


class AquiferUnits(BaseModel):
    env: str = "PROD"

    aquifer_code: str = "%"
    aquifer_name: str = "%"

    def find_aquifer_codes(self):
        db = connect_to_sageodata(service_name=self.env)
        df = db.query(
            f"select * from ( "
            f"select su.map_symbol || hu.hydro_subunit_code as aquifer_code, "
            f"hu.hydro_subunit_desc "
            f"from wa_hydrostrat_subunit hu left join st_strat_unit su on hu.strat_unit_no = su.strat_unit_no "
            f") "
            f"where aquifer_code like '{self.aquifer_code}' "
            f"and upper(hydro_subunit_desc) like upper('{self.aquifer_name}')"
        )
        return list(df.aquifer_code.values)
