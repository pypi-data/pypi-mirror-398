from datetime import datetime
import logging
import fnmatch

import pandas as pd
from pydantic import BaseModel

from dew_gwdata import sageodata as connect_to_sageodata
from dew_gwdata.webapp import utils as webapp_utils


logger = logging.getLogger(__name__)


class Wells(BaseModel):
    env: str = "PROD"

    # SEARCH FOR WELLS - GROUPED EXCLUSIVELY
    # --------------------------------------

    # Group 1 - search by ID
    idq: str = ""
    idq_unit_no: bool = True
    idq_dh_no: bool = False
    idq_obs_no: bool = True
    idq_dh_no_as_req: bool = True
    # Additionally, optionally, find wells within X of the first match
    idq_distance: float = 0

    # Group 2 - search by direct reference to drillhole numbers
    url_str: str = ""

    # Group 3 - search by fragment of drillhole name
    name_fragment: str = ""

    # Group 4 - search wells by date of salinity sample creation
    salinity_creation_date: str = ""
    salinity_created_by: str = ""

    wl_creation_date: str = ""
    wl_created_by: str = ""
    wl_measured_during: str = ""

    # Group 5 - search by strat unit (in logs)
    strat_map_symbol: str = ""
    strat_unit_no: int = 0

    # Group 6 - search by hydrostrat log unit
    hydrostrat_aquifer_code: str = ""
    hydro_strat_unit_no: int = 0
    hydro_subunit_code: str = ""

    # Group 7 - search by current aquifer monitored code
    aq_mon: str = ""

    # Group 8 - Find wells by aquifer code part (current or historical)
    aquifer_code: str = ""
    include_historical_aquifers: bool = False

    # Group 9 - find wells by group code
    group_code: str = ""
    swl_status: str = "C,H,N"
    tds_status: str = "C,H,N"
    swl_freq: str = "1,2,3,4,6,12,24,R,S,blank"
    tds_freq: str = "1,2,3,4,6,12,24,R,S,blank"
    swl_tds_combine: str = "and"
    filter_group_comment: str = "*"

    # Group 10 - arbitrary SQL
    sql: str = ""

    # Group 11 - construction dates
    completion_date_from: str = ""
    completion_date_to: str = ""

    status_code: str = ""

    edit_type: str = ""
    edit_timestamp: str = ""
    edit_by: str = ""

    # FILTER OPTIONS - reduce list of wells through filter options
    # ------------------------------------------------------------

    filter_aq_mon: str = ""
    filter_aquifer_code: str = ""
    filter_latest_tds_above: float = 0
    filter_latest_tds_below: float = 0
    filter_latest_sal_date_since: str = ""
    filter_log_types: str = ""
    filter_log_types_bool: str = "or"

    # SORT OPTIONS
    # ------------

    # To be implemented

    sort: str = "unit_long"
    order: str = "ascending"

    # OTHER OPTIONS
    # -------------
    error_message: str = ""

    def find_wells(self):
        db = connect_to_sageodata(service_name=self.env)

        # PRE-PROCESS SEARCH OPTIONS
        # --------------------------

        if self.strat_map_symbol and not self.strat_unit_no:
            df = db.strat_unit_by_map_symbol(self.strat_map_symbol)
            if len(df):
                self.strat_unit_no = df.map_symbol.iloc[0]
        if self.hydrostrat_aquifer_code and not (
            self.hydro_strat_unit_no and self.hydro_subunit_code
        ):
            df = db.strat_unit_by_map_symbol(self.strat_map_symbol)
            if len(df):
                self.strat_unit_no = df.map_symbol.iloc[0]

        self.group_code = self.group_code.upper()

        # SEARCH FOR WELLS
        # ----------------
        wells = None

        if self.idq.strip():
            logger.debug(f"Running Wells query for idq={self.idq}")
            id_types = []
            if self.idq_unit_no:
                id_types.append("unit_no")
            if self.idq_obs_no:
                id_types.append("obs_no")
            if self.idq_dh_no:
                id_types.append("dh_no")

            logger.debug(f"id_types requested: {id_types}")

            if self.idq_dh_no_as_req:
                # Try and search dh_no only if there is no result
                wells = db.find_wells(
                    self.idq, types=[t for t in id_types if not t == "dh_no"]
                )
                if len(wells) == 0:
                    wells = db.find_wells(self.idq, types=id_types)
            else:
                wells = db.find_wells(self.idq, types=id_types)

            if self.idq_distance > 0:
                wells = db.drillhole_within_distance(wells.dh_no[0], self.idq_distance)
            else:
                wells = db.drillhole_details(wells.dh_no)

            x = str(self.idq)
            if len(x) > 12:
                x = x[:9] + "..."

            query_params = [
                f"idq={self.idq}",
                f"idq_unit_no={int(self.idq_unit_no)}",
                f"idq_obs_no={int(self.idq_obs_no)}",
                f"idq_dh_no={int(self.idq_dh_no)}",
                f"idq_dh_no_as_req={int(self.idq_dh_no_as_req)}",
            ]

            if self.idq_distance:
                name = f"Wells within {self.idq_distance} km of '{x}'"
                name_safe = f"{self.idq_distance}km_from_" + x.replace(" ", "_")
                query_params.append(f"idq_distance={self.idq_distance:.3f}")
            else:
                name = f"Search '{x}'"
                name_safe = "search_" + x.replace(" ", "_")

        elif self.url_str:
            logger.debug(f"Running Wells query for url_str={self.url_str}")
            dh_nos = webapp_utils.urlstr_to_dhnos(self.url_str)
            wells = db.drillhole_details(dh_nos)
            name = f"Direct selection"
            name_safe = self.url_str
            query_params = [f"url_str={self.url_str}"]

        elif self.name_fragment:
            logger.debug(f"Running Wells query for name_fragment={self.name_fragment}")
            wells = db.drillhole_details_by_name_search(self.name_fragment)
            name = f"Search for '{self.name_fragment}'"
            name_safe = f"search_{self.name_fragment}"
            query_params = [f"name_fragment={self.name_fragment}"]

        elif self.salinity_creation_date and self.salinity_created_by:
            logger.debug(
                f"Running Wells query for salinity_creation_date={self.salinity_creation_date} and salinity_created_by={self.salinity_created_by}"
            )
            tstamp = pd.Timestamp(self.salinity_creation_date)
            tstamp_ymd = tstamp.strftime("%Y-%m-%d")
            wells = db.query(
                "select s.drillhole_no as dh_no from sm_sample s "
                "join dd_drillhole d on s.drillhole_no = d.drillhole_no "
                f"where s.creation_date >= to_date('{tstamp_ymd} 00:00', 'YYYY-MM-DD HH24:MI') "
                f"and s.creation_date <= to_date('{tstamp_ymd} 23:59', 'YYYY-MM-DD HH24:MI') "
                f"and s.created_by like '{self.salinity_created_by}' "
                "and d.deletion_ind = 'N' and s.sample_type = 'S' "
            )
            wells = db.drillhole_details(wells)
            name = f"Search for wells with salinity data created on {tstamp.strftime('%d/%m/%y')} by {self.salinity_created_by}"
            name_safe = f"search_tds_{self.salinity_created_by}_{tstamp_ymd}"
            query_params = [
                f"salinity_creation_date={self.salinity_creation_date}",
                f"salinity_created_by={self.salinity_created_by}",
            ]

        elif self.wl_creation_date and self.wl_created_by and self.wl_measured_during:
            logger.debug(
                f"Running Wells query for wl_creation_date={self.wl_creation_date} and wl_created_by={self.wl_created_by} and wl_measured_ruing={self.wl_measured_during}"
            )
            tstamp = pd.Timestamp(self.wl_creation_date)
            tstamp_ymd = tstamp.strftime("%Y-%m-%d")
            wells = db.query(
                f"""
            select drillhole_no as dh_no
            from wa_water_level  
            where creation_date >= to_date('{tstamp_ymd} 00:00', 'YYYY-MM-DD HH24:MI')
                  and creation_date <= to_date('{tstamp_ymd} 23:59', 'YYYY-MM-DD HH24:MI')
                  and created_by like '{self.wl_created_by}'
                  and measured_during = '{self.wl_measured_during}'
            """
            )
            wells = db.drillhole_details(wells)
            name = f"Search for wells with WL data created {tstamp.strftime('%d/%m/%y')} by {self.wl_created_by} measured during {self.wl_measured_during}"
            name_safe = f"search_wl_{self.wl_created_by}_{tstamp_ymd}_measured_{self.wl_measured_during}"
            query_params = [
                f"wl_creation_date={self.wl_creation_date}",
                f"wl_created_by={self.wl_created_by}",
                f"wl_measured_during={self.wl_measured_during}",
            ]

        elif self.strat_unit_no:
            logger.debug(f"Running Wells query for strat_unit_no={self.strat_unit_no}")
            wells = db.strat_logs_by_strat_unit([self.strat_unit_no])
            st = db.strat_unit_details([self.strat_unit_no])
            if len(st) > 0:
                st = st.iloc[0]
            name = f"Search for '{st.map_symbol}' in a strat log"
            name_safe = f"search_strat_unit_{st.map_symbol}"
            query_params = [f"strat_unit_no={self.strat_unit_no}"]

        elif self.hydro_strat_unit_no:
            logger.debug(
                f"Running Wells query for hydro_strat_unit_no={self.hydro_strat_unit_no}"
            )
            wells = db.hydrostrat_logs_by_strat_unit([self.hydro_strat_unit_no])
            st = db.strat_unit_details([self.hydro_strat_unit_no])
            if len(st) > 0:
                st = st.iloc[0]
            name = f"Search for '{st.map_symbol}' in a hydrostrat log"
            name_safe = f"search_hydro_strat_unit_{st.map_symbol}"
            query_params = [f"hydro_strat_unit_no={self.hydro_strat_unit_no}"]

        elif self.group_code:
            logger.debug(f"Running Wells query for group_code={self.group_code}")
            wells = db.wells_in_groups([self.group_code])

            wells["dh_comments"] = wells.dh_comments.fillna("")

            swl_freqs = [f.strip() for f in self.swl_freq.split(",")]
            tds_freqs = [f.strip() for f in self.tds_freq.split(",")]
            swl_statuses = [s.strip() for s in self.swl_status.split(",")]
            tds_statuses = [s.strip() for s in self.tds_status.split(",")]
            if "blank" in swl_freqs:
                swl_freqs.append(None)
            if "blank" in tds_freqs:
                tds_freqs.append(None)

            # wells = wells[wells.swl_freq.isin(swl_freqs)]
            # wells = wells[wells.tds_freq.isin(tds_freqs)]
            # wells = wells[wells.swl_status.isin(swl_statuses)]
            # wells = wells[wells.tds_status.isin(tds_statuses)]

            swl_wells = wells[
                wells.swl_status.isin(swl_statuses) & wells.swl_freq.isin(swl_freqs)
            ].dh_no
            tds_wells = wells[
                wells.tds_status.isin(tds_statuses) & wells.tds_freq.isin(tds_freqs)
            ].dh_no
            if self.swl_tds_combine.lower() == "and":
                wells = wells[wells.dh_no.isin(swl_wells) & wells.dh_no.isin(tds_wells)]
                print(f"reduced to {len(wells)} because swl_tds_combine == and")
            elif self.swl_tds_combine.lower() == "or":
                wells = wells[wells.dh_no.isin(swl_wells) | wells.dh_no.isin(tds_wells)]
                print(f"reduced to {len(wells)} because swl_tds_combine == and")

            wells = wells[
                wells.apply(
                    lambda row: fnmatch.fnmatch(
                        row.dh_comments, self.filter_group_comment
                    ),
                    axis=1,
                )
            ]
            name = f"Search group '{self.group_code}'"
            name_safe = f"search_group_{self.group_code}"
            query_params = [
                f"group_code={self.group_code}",
                f"filter_group_comment={self.filter_group_comment}",
                f"swl_status={self.swl_status}",
                f"tds_status={self.tds_status}",
                f"swl_freq={self.swl_freq}",
                f"tds_freq={self.tds_freq}",
                f"swl_tds_combine={self.swl_tds_combine}",
            ]

        elif self.aq_mon:
            logger.debug(f"Running Wells query for aq_mon={self.aq_mon}")
            wells = db.drillholes_by_full_current_aquifer([self.aq_mon])
            name = f"Search for exact aquifer '{self.aq_mon}'"
            name_safe = f"search_exact_aquifer_{self.aq_mon}"
            query_params = [f"aq_mon={self.aq_mon}"]

        elif self.aquifer_code:
            logger.debug(
                f"Running Wells query for aquifer_code={self.aquifer_code} and include_historical_aquifers={self.include_historical_aquifers}"
            )
            wells = db.drillholes_by_aquifer_all([self.aquifer_code])
            logger.debug(
                f"Initial query using drillholes_by_aquifer_all resulted in {len(wells)} wells for {self.aquifer_code}"
            )
            if not self.include_historical_aquifers:
                logger.debug(f"Restricting only to current aquifer codes.")
                wells = wells[
                    wells.current_aquifer.str.contains(
                        f"{self.aquifer_code}", regex=False
                    )
                ]
                logger.debug(
                    f"resulted in {len(wells)} with current aquifer_code = {self.aquifer_code}"
                )
            name = f"Search for aquifer '{self.aquifer_code}'"
            name_safe = f"search_aquifer_{self.aquifer_code}"
            query_params = [
                f"aq_mon={self.aquifer_code}",
                f"include_historical_aquifers={int(self.include_historical_aquifers)}",
            ]

        elif self.status_code:
            logger.debug(f"Running Wells query for status_codes={self.status_code}")
            status_codes = [s.strip().upper() for s in self.status_code.split(",")]
            wells = db.drillholes_by_status(status_codes)
            name = f"Search for wells with historical status"
            name_safe = f"search_status_hist_{self.status_code}"
            query_params = [f"status_code={self.status_code}"]

        elif self.sql:
            logger.debug(f"Running Wells query for arbitrary SQL:\n{self.sql}")
            wells = db.query(self.sql)
            # logger.debug(f"Search by arbitrary SQL. query = \n{self.sql}\nResult length = {len(wells)}:\n{wells.head()}")
            if not "dh_no" in wells:
                wells = wells.rename(columns={"drillhole_no": "dh_no"})
            name = f"Search by arbitrary SQL"
            name_safe = f"search_arbitrary_sql"
            query_params = [f"sql={self.sql}"]

        elif self.completion_date_from or self.completion_date_to:
            logger.debug(
                f"Running Wells query for completion dates between {self.completion_date_from} and {self.completion_date_to}"
            )
            if not self.completion_date_from:
                completion_date_from = "1800-01-01"
            else:
                completion_date_from = pd.Timestamp(self.completion_date_from).strftime(
                    "%Y-%m-%d"
                )
            if not self.completion_date_to:
                completion_date_to = datetime.now().strftime("%Y-%m-%d")
            else:
                completion_date_to = pd.Timestamp(self.completion_date_to).strftime(
                    "%Y-%m-%d"
                )
            sql = (
                "select d.drillhole_no as dh_no from dd_drillhole d join dc_construction c on d.drillhole_no = c.drillhole_no "
                f"where c.completion_date >= to_date('{completion_date_from} 00:00', 'YYYY-MM-DD HH24:MI') "
                f"and c.completion_date <= to_date('{completion_date_to} 23:59', 'YYYY-MM-DD HH24:MI') "
                f"and c.constrn_flag = 'C' "
                "and d.deletion_ind = 'N' "
            )
            logger.debug(f"Completion date query. SQL:\n{sql}")
            wells = db.query(sql)
            logger.debug(f"Found {len(wells)} results")
            name = f"Search by wells constructed between {self.completion_date_from} and {self.completion_date_to}"
            name_safe = f"search_completion_date_btwn"
            query_params = [
                f"completion_date_from={self.completion_date_from}",
                f"completion_date_to={self.completion_date_to}",
            ]

        elif self.edit_timestamp and self.edit_by:
            logger.debug(
                f"Running Wells query for last edited by {self.edit_by} on {self.edit_timestamp}"
            )
            edit_timestamp = pd.Timestamp(self.edit_timestamp).strftime("%Y-%m-%d")
            if self.edit_type == "aquifer_mon":
                logger.debug(f"... edit topic, aquifer monitored")
                query2 = f"""
                select aq.drillhole_no as dh_no
                from dd_dh_aquifer_mon aq
                where 
                    coalesce(aq.modified_date, aq.creation_date) >= to_date('{edit_timestamp} 00:00', 'YYYY-MM-DD HH24:MI')
                    and coalesce(aq.modified_date, aq.creation_date) <= to_date('{edit_timestamp} 23:59', 'YYYY-MM-DD HH24:MI')
                    and coalesce(aq.modified_by, aq.created_by) = '{self.edit_by}'
                """
                wells = db.query(query2)

            logger.debug(f"Found {len(wells)} wells with this edit activity occurring")
            name = f"Wells with edits to {self.edit_type} by {self.edit_by} on {edit_timestamp}"
            name_safe = f"edit_{self.edit_type}"
            query_params = [
                f"edit_type={self.edit_type}",
                f"edit_timestamp={self.edit_timestamp}",
                f"edit_by={self.edit_by}",
            ]
        else:
            logger.debug(f"Running Wells query for an empty search.")
            wells = db.drillhole_details([0])
            name = f"Empty search"
            name_safe = f"empty"
            query_params = [
                f"idq=",
                f"idq_unit_no=1",
                f"idq_obs_no=1",
                f"idq_dh_no=0",
                f"idq_dh_no_as_req=0",
            ]
            self.error_message = "Please enter a search query in one of the boxes under the 'Query form' above."

        # FILTER
        # ------
        # deal with the empty case
        if len(wells) == 0:
            wells = [0]

        wells = db.wells_summary(wells)
        wells = wells.fillna(
            value={
                "filter_aquifer_code": "",
                "filter_aq_mon": "",
            }
        )  # otherwise the filtering breaks.

        if self.filter_aq_mon:
            logger.debug(f"Filtering to aq_mon {self.filter_aq_mon}")
            logger.debug(f"- before: {len(wells)} records")
            wells = wells[wells.aquifer == self.filter_aq_mon]
            logger.debug(f"- after: {len(wells)} records")
            query_params.append(f"filter_aq_mon={self.filter_aq_mon}")

        if self.filter_aquifer_code:
            logger.debug(
                f"Filtering to wells containing aquifers {self.filter_aquifer_code}"
            )
            aquifer_codes = self.filter_aquifer_code.split(",")
            aquifer_codes = set([a.strip() for a in aquifer_codes])
            logger.debug(f" - query interpreted as aquifers: {list(aquifer_codes)}")
            wells["aquifer_list"] = wells.aquifer.str.split("+")
            indices = []
            for idx, row in wells[["dh_no", "aquifer_list"]].iterrows():
                if len(aquifer_codes.intersection(row.aquifer_list)) >= 1:
                    indices.append(idx)
            logger.debug(f"- before: {len(wells)} records")
            wells = wells.loc[indices]
            # wells = wells[
            #     wells.aquifer.str.contains(self.filter_aquifer_code, na=False)
            # ]
            logger.debug(f"- after: {len(wells)} records")
            query_params.append(f"filter_aquifer_code={self.filter_aquifer_code}")

        if self.filter_latest_tds_above:
            logger.debug(
                f"Filtering to latest_tds_above {self.filter_latest_tds_above}"
            )
            logger.debug(f"- before: {len(wells)} records")
            wells = wells[wells.latest_tds >= self.filter_latest_tds_above]
            logger.debug(f"- after: {len(wells)} records")
            query_params.append(
                f"filter_latest_tds_above={self.filter_latest_tds_above}"
            )

        if self.filter_latest_tds_below:
            logger.debug(
                f"Filtering to latest_tds_below {self.filter_latest_tds_below}"
            )
            logger.debug(f"- before: {len(wells)} records")
            wells = wells[wells.latest_tds <= self.filter_latest_tds_below]
            logger.debug(f"- after: {len(wells)} records")
            query_params.append(
                f"filter_latest_tds_below={self.filter_latest_tds_below}"
            )

        if self.filter_latest_sal_date_since:
            logger.debug(
                f"Filtering to latest salinity date >= {self.filter_latest_sal_date_since}"
            )
            logger.debug(f"- before: {len(wells)} records")
            filter_latest_sal_date_since = pd.Timestamp(
                self.filter_latest_sal_date_since
            )
            wells = wells[
                wells.latest_sal_date.dt.date >= filter_latest_sal_date_since.date()
            ]
            logger.debug(f"- after: {len(wells)} records")
            query_params.append(
                f"filter_latest_sal_date_since={self.filter_latest_sal_date_since}"
            )

        if self.filter_log_types.strip():
            logger.debug(
                f"Filtering to wells containing log types {self.filter_log_types}"
            )
            if self.filter_log_types_bool.lower() == "or":
                logger.debug(f"combining by OR")
                dh_nos = []
                if "D" in self.filter_log_types.upper():
                    dh_nos += list(wells[wells.db_drillers_log == "Y"].dh_no)
                if "L" in self.filter_log_types.upper():
                    dh_nos += list(wells[wells.db_lith_log == "Y"].dh_no)
                if "S" in self.filter_log_types.upper():
                    dh_nos += list(wells[wells.db_strat_log == "Y"].dh_no)
                if "H" in self.filter_log_types.upper():
                    dh_nos += list(wells[wells.db_hydrostrat_log == "Y"].dh_no)
                wells = wells[wells.dh_no.isin(dh_nos)]
            elif self.filter_log_types_bool.lower() == "and":
                logger.debug(f"combining by AND")
                if "D" in self.filter_log_types.upper():
                    wells = wells[wells.db_drillers_log == "Y"]
                if "L" in self.filter_log_types.upper():
                    wells = wells[wells.db_lith_log == "Y"]
                if "S" in self.filter_log_types.upper():
                    wells = wells[wells.db_strat_log == "Y"]
                if "H" in self.filter_log_types.upper():
                    wells = wells[wells.db_hydrostrat_log == "Y"]
            query_params += [
                f"filter_log_types={self.filter_log_types}",
                f"filter_log_types_bool={self.filter_log_types_bool}",
            ]

        # SORT
        # ----

        if self.sort == "Drillhole number":
            wells = wells.sort_values("dh_no")
            query_params.append("sort=dh_no")
        elif self.sort == "Unit number":
            wells = wells.sort_values("unit_long")
            query_params.append("sort=unit_long")
        elif self.sort == "Drillhole name":
            wells = wells.sort_values("dh_name")
            query_params.append("sort=dh_name")

        if self.order == "ascending":
            query_params.append("order=ascending")
        elif self.order == "descending":
            wells = wells[::-1]
            query_params.append("order=descending")

        name += f" ({len(wells)} wells)" if len(wells) != 1 else " (1 well)"
        if len(wells) == 1 and self.url_str:
            name_safe = f"dh_{wells.dh_no[0]}"
        name_safe = name_safe[:30]
        query_params.append(f"env={self.env}")

        logger.debug(f"query found {len(wells)} drillholes. Returning.")

        return wells, name, name_safe, "&".join(query_params)
