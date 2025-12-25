from pathlib import Path
import urllib.parse
import re

import numpy as np
import pandas as pd
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import lasio
from sageodata_db import connect as connect_to_sageodata
import pozo

import dew_gwdata as gd

from dew_gwdata.webapp import utils as webapp_utils


router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


def get_well_metadata(df, dh_no, env="prod"):
    cols = [
        "dh_no",
        "unit_hyphen",
        "obs_no",
        "dh_name",
        "aquifer",
    ]

    def check_columns():
        for col in cols:
            if not col in df.columns:
                return False
        return True

    if len(df) and check_columns():
        result = df[cols].iloc[0]
    else:
        db = connect_to_sageodata(service_name=env)
        result = db.wells_summary([dh_no])[cols].iloc[0]
    result["title"] = webapp_utils.make_dh_title(result)
    return result


def format_well_title(well):
    if well.obs_no:
        return " / ".join([well.obs_no, well.unit_hyphen])
    else:
        return well.title


@router.get("/well_summary")
def well_summary(request: Request, dh_no: int, env: str = "prod") -> str:
    db = connect_to_sageodata(service_name=env)
    well = db.wells_summary([dh_no]).iloc[0]
    groups = db.drillhole_groups([dh_no]).pipe(gd.cleanup_columns)
    notes = db.drillhole_notes([dh_no]).sort_values(["note_date"], ascending=True)
    status = db.drillhole_status([dh_no]).sort_values(["status_date"], ascending=False)
    geophyslogs = db.geophys_log_metadata([dh_no]).sort_values(
        "logged_date", ascending=True
    )
    aqmon = db.aquifers_monitored([dh_no]).sort_values(
        ["aquifer_mon_from"], ascending=False
    )
    files = db.drillhole_file_list([dh_no])
    refs = db.drillhole_document_references([dh_no])
    const = db.construction_events([dh_no]).sort_values(
        "completion_date", ascending=True
    )
    const = gd.add_construction_activity_column(const)
    const["auto_dwcr"] = const.apply(
        lambda row: (
            f"<a href='/api/well_auto_dwcr?dh_no={row.dh_no}&completion_no={row.completion_no}&env={env}'>Auto DWCR</a>"
            if row.event_type == "C"
            else ""
        ),
        axis=1,
    )
    elev = db.elevation_surveys([dh_no]).assign(**{"ref_height [calculated]": pd.NA})
    elev.loc[
        (~pd.isnull(elev.ground_elev)) & (~pd.isnull(elev.ref_elev)),
        "ref_height [calculated]",
    ] = (
        elev.ref_elev - elev.ground_elev
    )
    groups["group_code"] = groups.group_code.apply(
        lambda grp: f"<a href='/app/group_summary?group_code={grp}&env={env}'>{grp}</a>"
    )
    groups["sort_key"] = groups.group_type.map(
        {"OMN": 0, "PR": 1, "OMH": 2, "GDU": 3, "MDU": 4}
    )
    groups = groups.sort_values(["sort_key", "group_modified_date"])
    groups = groups.drop(
        [
            "well_id",
            "sort_key",
            "dh_created_by",
            "dh_creation_date",
            "dh_modified_by",
            "dh_modified_date",
            "group_created_by",
            "group_creation_date",
            "group_modified_by",
            "group_modified_date",
        ],
        axis=1,
    )

    files["file_name"] = files.apply(
        lambda row: f"<a href='/api/db_file?file_no={row.file_no}'>{row.file_name}</a>",
        axis=1,
    )
    geophyslogs["job_no"] = geophyslogs.job_no.apply(
        lambda job_no: f"<a href='/app/well_geophysical_logs?dh_no={dh_no}&env={env}#{job_no}'>{job_no}</a>"
    )
    const["permit_no"] = const.permit_no.apply(
        lambda pn: (
            f"<a href='/app/permit?permit_no={pn}&env={env}'>{pn}</a>" if pn else ""
        )
    )
    const["completion_date_str"] = const.completion_date.apply(
        lambda d: d.strftime("%d/%m/%Y") if not pd.isnull(d) else ""
    )
    const["completion_date"] = const.apply(
        lambda row: f"<a href='/app/well_construction?dh_no={dh_no}&env={env}#{row.completion_no}'>{row.completion_date_str}</a>",
        axis=1,
    )

    wls = db.water_levels([dh_no])
    cols_for_record = [
        "js_date",
        "dtw",
        "swl",
        "rswl",
        "anomalous_ind",
        "pumping_ind",
        "artesian_ind",
        "measured_during",
        "pressure",
        "sip",
        "sit",
        "temperature",
        "comments",
        "datasource",
    ]
    chart_rows = []
    chart_wls = wls.dropna(subset=["swl", "obs_date"], how="any")
    wl_chart_from = ""
    wl_chart_to = ""
    if len(chart_wls):
        for idx, record in chart_wls.sort_values("obs_date").iterrows():
            record = record.to_dict()
            record["js_date"] = record["obs_date"].strftime(
                f'new Date("%Y-%m-%dT%H:%M")'
            )
            row_values = [
                webapp_utils.fmt_for_js(record[col]) for col in cols_for_record
            ]
            row = "[" + ", ".join(row_values) + "]"
            chart_rows.append(row)
        wl_chart_from = chart_wls.obs_date.dt.strftime("%Y").min()
        wl_chart_to = chart_wls.obs_date.dt.strftime("%Y").max()
    wl_js_dataset = ",\n ".join(chart_rows)

    sals = db.salinities([dh_no])
    cols_for_record = [
        "js_date",
        "ec",
        "tds",
        "anomalous_ind",
        "measured_during",
        "extract_method",
        "depth_from",
        "comments",
    ]
    chart_rows = []
    sal_chart_from = ""
    sal_chart_to = ""
    chart_sals = sals.dropna(subset=["ec", "collected_date", "tds"], how="any")
    if len(chart_sals):
        for idx, record in chart_sals.sort_values("collected_date").iterrows():
            record = record.to_dict()
            record["js_date"] = record["collected_date"].strftime(
                f'new Date("%Y-%m-%dT%H:%M")'
            )
            row_values = [
                webapp_utils.fmt_for_js(record[col]) for col in cols_for_record
            ]
            row = "[" + ", ".join(row_values) + "]"
            chart_rows.append(row)
        sal_chart_from = chart_sals.collected_date.dt.strftime("%Y").min()
        sal_chart_to = chart_sals.collected_date.dt.strftime("%Y").max()
    sal_js_dataset = ",\n ".join(chart_rows)

    wdb = gd.connect_to_package_database()
    usage = pd.read_sql(
        f"select * from usage where unit_hyphen = '{well.unit_hyphen}' and month is null",
        wdb,
    )
    usage = usage.sort_values(["calendar_year", "financial_year"])
    if len(usage.calendar_year.dropna()) > len(usage.financial_year.dropna()):
        usage_year_col = "calendar_year"
    else:
        usage_year_col = "financial_year"

    cols_for_record = ["js_date", "effective_kl"]
    chart_rows = []
    for idx, record in usage.iterrows():
        record = record.to_dict()
        record["js_date"] = record[usage_year_col]
        row_values = [webapp_utils.fmt_for_js(record[col]) for col in cols_for_record]
        row = "[" + ", ".join(row_values) + "]"
        chart_rows.append(row)
    usage_js_dataset = ",\n ".join(chart_rows)

    def make_envelope_link_old_sarig(ref_id):
        try:
            int_ref_id = int(ref_id)
        except:
            return ref_id
        else:
            url = "https://sarigbasis.pir.sa.gov.au/WebtopEw/ws/samref/sarig1/cat2/ResultSet"
            tag = f"<a href='{url}?w=NATIVE%28%27allfields%2Ctext+ph+is+%27%27Env+{int_ref_id:05.0f}%27%27%27%29'>"
            img = '<img src="/static/external-link.svg" width="14px" height="14px" />'
            return f"{tag}{img}</a>"

    def make_envelope_link_new_sarig_catalogue(row):
        search_term = f'"{row.ref_type} {row.ref_id}"'
        search_term = search_term.strip()
        if search_term:
            url = f"https://catalog.sarig.sa.gov.au/dataset/?ext_date_facet=&ext_search_notes={search_term}&ext_advanced_operator=OR&sort=score+desc%2C+metadata_modified+desc&ext_or_facet_extra_or_type=on&ext_bbox="
            tag = f"<a href='{url}' target='blank'>"
            img = '<img src="/static/external-link.svg" width="14px" height="14px" />'
            return f"{tag}{img}</a>"
        else:
            return ""

    refs.loc[refs.ref_type == "ENV", "old_sarig"] = refs.ref_id.apply(
        make_envelope_link_old_sarig
    )
    refs["new_sarig"] = refs.apply(make_envelope_link_new_sarig_catalogue, axis=1)

    well["nearest_rainfall_site"] = (
        f"<a href='/app/rainfall_stations?nearest_to_well={well.unit_hyphen}'><img src='/static/external-link.svg' width=12 height=12 /></a>"
    )
    well["aquifer_link"] = ""
    if well["aquifer"]:
        well["aquifer_link"] = (
            f"<a href='/app/aquifer_unit?aquifer_code={well.aquifer}&env={env}'>{well.aquifer}</a>"
        )

    well_cols = [
        "dh_no",
        "unit_hyphen",
        "unit_long",
        "obs_no",
        "dh_name",
        "dh_other_name",
        "aquifer",
        "aquifer_link",
        # "suburb",
        "nearest_rainfall_site",
        "comments",
        "water_point",
        "water_point_type",
        "easting",
        "northing",
        "zone",
        "latitude",
        "longitude",
        "purpose",
        "pwa",
        "hundred",
        "landscape",
        "owner",
        "drill_method",
        "orig_drilled_depth",
        "orig_drilled_date",
        "max_drilled_depth",
        "max_drilled_depth_date",
        "latest_open_depth",
        "latest_open_depth_date",
        "latest_cased_from",
        "latest_cased_to",
        "latest_casing_min_diam",
        "latest_dtw",
        "latest_swl",
        "latest_rswl",
        "latest_dry",
        "latest_wl_date",
        "latest_ec",
        "latest_tds",
        "latest_sal_date",
        "latest_yield",
        "latest_yield_date",
        "latest_yield_extract_meth",
        "latest_yield_duration",
        "latest_yield_meth",
        "latest_ref_elev",
        "latest_elev_date",
        "state_asset",
        "state_asset_status",
        "state_asset_retained",
        "owner_code",
        "state_asset_comments",
        "engineering_dh",
        "water_well",
        "mineral_dh",
        "petroleum_well",
        "seismic_dh",
        "stratigraphic_dh",
        "survey_horiz_accuracy",
        "survey_horiz_meth",
        "nrm",
        "latest_ph",
        "latest_ph_date",
        "replaced_date",
        "parent_dh_no",
        "child_dh_no",
    ]
    elev_cols = [
        "elev_date",
        "applied_date",
        "ground_elev",
        "ref_elev",
        "ref_height [calculated]",
        "survey_meth",
        "ref_point_type",
        "comments",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    notes_cols = [
        "note_no",
        "note_date",
        "author",
        "note",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    status_cols = [
        "status_date",
        "status_code",
        "status_desc",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    aqmon_cols = [
        "current_aquifer",
        "aquifer_mon_from",
        "aquifer_mon",
        "aquifer_desc",
        "comments",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    files_cols = [
        "file_no",
        "file_name",
        "file_type_code",
        "comments",
        "file_doc_type_code",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    geophyslogs_cols = [
        "job_no",
        "logged_date",
        "client",
        "purpose",
        "operators",
        "vehicle",
        "max_log_depth",
        "comments",
    ]
    const_cols = [
        "completion_date",
        "event_type",
        "activity",
        "permit_no",
        "wcr_id",
        "auto_dwcr",
        "driller_name",
        "driller_class",
        "current_depth",
        "drill_method",
        "casing_to",
        "casing_material",
        "casing_min_diam",
        "comments",
        "pzone_type",
        "pzone_from",
        "pzone_to",
    ]
    refs_cols = [
        "info_type",
        "info_title",
        "ref_type",
        "ref_id",
        "old_sarig",
        "new_sarig",
        "ref_title",
        "ref_publication",
    ]

    well["title"] = webapp_utils.make_dh_title(well)
    well_table = webapp_utils.series_to_html(well[well_cols])
    groups_table = webapp_utils.frame_to_html(groups)
    elev_table = webapp_utils.frame_to_html(elev[elev_cols])
    notes_table = webapp_utils.frame_to_html(notes[notes_cols])
    status_table = webapp_utils.frame_to_html(status[status_cols])
    aqmon_table = webapp_utils.frame_to_html(aqmon[aqmon_cols])
    files_table = webapp_utils.frame_to_html(files[files_cols])
    geophyslogs_table = webapp_utils.frame_to_html(geophyslogs[geophyslogs_cols])
    const_table = webapp_utils.frame_to_html(const[const_cols])
    refs_table = webapp_utils.frame_to_html(refs[refs_cols].drop_duplicates())

    return templates.TemplateResponse(
        "well_summary.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "groups": groups,
            "elev": elev,
            "notes": notes,
            "status": status,
            "aqmon": aqmon,
            "files": files,
            "const": const,
            "refs": refs,
            "geophyslogs": geophyslogs,
            "well_table": well_table,
            "groups_table": groups_table,
            "elev_table": elev_table,
            "notes_table": notes_table,
            "status_table": status_table,
            "aqmon_table": aqmon_table,
            "files_table": files_table,
            "geophyslogs_table": geophyslogs_table,
            "const_table": const_table,
            "refs_table": refs_table,
            "wl_js_dataset": wl_js_dataset,
            "sal_js_dataset": sal_js_dataset,
            "wl_chart_from": wl_chart_from,
            "wl_chart_to": wl_chart_to,
            "sal_chart_from": sal_chart_from,
            "sal_chart_to": sal_chart_to,
            "usage_js_dataset": usage_js_dataset,
            "usage_year_col": usage_year_col,
        },
    )


@router.get("/well_manual_water_level")
def well_manual_water_level(
    request: Request,
    dh_no: int,
    param: str = "swl",
    ignore_anomalous: bool = False,
    ignore_pumping: bool = False,
    keep_measured_during: str = "",
    trend_param: str = "",
    trend_period: str = "",
    env: str = "prod",
) -> str:
    db = connect_to_sageodata(service_name=env)
    df = db.water_levels([dh_no]).sort_values("obs_date", ascending=False)
    df["charted"] = "Y"
    if ignore_anomalous:
        df.loc[df.anomalous_ind == "Y", "charted"] = "N - anomalous"
    if ignore_pumping:
        df.loc[df.pumping_ind == "Y", "charted"] = "N - pumping"
    if keep_measured_during:
        df.loc[
            ~df.measured_during.isin(keep_measured_during.upper().split(",")), "charted"
        ] = f"N - measured_during not {keep_measured_during}"

    well = get_well_metadata(df, dh_no)

    table = webapp_utils.frame_to_html(gd.cleanup_columns(df, keep_cols=[]))

    cols_for_record = [
        "js_date",
        "dtw",
        "swl",
        "rswl",
        "anomalous_ind",
        "pumping_ind",
        "artesian_ind",
        "measured_during",
        "pressure",
        "sip",
        "sit",
        "temperature",
        "comments",
        "datasource",
    ]
    chart_rows = []
    for idx, record in (
        df[df.charted == "Y"]
        .dropna(subset=["swl", "obs_date"], how="any")
        .sort_values("obs_date")
        .iterrows()
    ):
        record = record.to_dict()
        record["js_date"] = record["obs_date"].strftime(f'new Date("%Y-%m-%dT%H:%M")')
        row_values = [webapp_utils.fmt_for_js(record[col]) for col in cols_for_record]
        row = "[" + ", ".join(row_values) + "]"
        chart_rows.append(row)
    wl_js_dataset = ",\n ".join(chart_rows)

    trend_js = ""
    trend = False
    if trend_param.lower() in ("dtw", "swl", "rswl"):
        trend_param = trend_param.lower()
        if trend_param in ("dtw", "swl"):
            direction = "reverse"
        else:
            direction = "normal"
        tdf = df[(df.charted == "Y")].dropna(
            subset=["obs_date", trend_param], how="any"
        )
        trend_start, trend_end = trend_period.split("-")
        trend_start = pd.Timestamp(trend_start)
        trend_end = pd.Timestamp(trend_end)
        tdf = tdf[(tdf.obs_date >= trend_start) & (tdf.obs_date <= trend_end)]
        if len(tdf):
            trendline = gd.linear_trend(
                tdf, x="obs_date", y=trend_param, direction=direction
            )
            trend_js_rows = []
            for tstamp, row in trendline.iterrows():
                js_row = [tstamp.strftime(f'new Date("%Y-%m-%dT%H:%M")'), row.trendline]
                trend_js_rows.append(
                    "[" + ", ".join([webapp_utils.fmt_for_js(v) for v in js_row]) + "]"
                )
            trend_js_data = "[" + ", ".join(trend_js_rows) + "]"
            trend_js = (
                ",\n\t\t{"
                + f"""
                name: '{trend_param} trendline',
                type: 'line',
                symbol: 'none',
                data: {trend_js_data},
                yAxisIndex: {0 if direction == "reverse" else 1},
                z: 50
            """
                + "}\n"
            )
            trend = trendline.iloc[0]

    return templates.TemplateResponse(
        "well_manual_water_level.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_manual_water_level",
            "singular_redirect_to": "well_manual_water_level",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "df": df,
            "wl_js_dataset": wl_js_dataset,
            "table": table,
            "param": param,
            "ignore_anomalous": ignore_anomalous,
            "ignore_pumping": ignore_pumping,
            "keep_measured_during": keep_measured_during,
            "trend_param": trend_param,
            "trend_period": trend_period,
            "trend_js": trend_js,
            "trend": trend,
        },
    )


@router.get("/well_logger_water_level")
def well_logger_water_level(
    request: Request,
    dh_no: int,
    param: str = "swl",
    freq: str = "1d",
    keep_grades: str = "1, 20, 30",
    max_gap_days: float = 1,
    start: str = "",
    finish: str = "",
    env: str = "prod",
    aqts_env: str = "prod",
) -> str:
    if not start:
        start = None
        start_str = ""
    else:
        start = gd.timestamp_acst(start)
        start_str = start.strftime("%Y-%m-%d")

    if not finish:
        finish = None
        finish_str = ""
    else:
        finish = gd.timestamp_acst(finish)
        finish_str = finish.strftime("%Y-%m-%d")

    keep_grades = [int(g) for g in keep_grades.split(",")] if keep_grades else []
    keep_grades_str = ", ".join([f"{g:.0f}" for g in sorted(keep_grades)])

    db = connect_to_sageodata(service_name=env)
    summ = db.wells_summary([dh_no])
    well = get_well_metadata(summ, dh_no)
    aq = gd.DEWAquarius(env=aqts_env)
    dfs = aq.fetch_timeseries_data(
        well.unit_hyphen,
        param=param,
        freq=freq,
        max_gap_days=max_gap_days,
        start=start,
        finish=finish,
        keep_grades=keep_grades,
    )

    chart_rows = []
    df = gd.join_logger_data_intervals(dfs)
    for idx, record in df.iterrows():
        record = record.to_dict()
        record["js_date"] = record["timestamp"].strftime(f'new Date("%Y/%m/%d %H:%M")')
        row_values = [record["js_date"]]

        wl_value = record[param]
        if pd.isnull(wl_value) or wl_value == "NaT" or str(wl_value) == "nan":
            wl_value = "NaN"
        else:
            wl_value = f"{wl_value:.3f}"
        row_values.append(wl_value)

        grade_value = record["grade"]
        if pd.isnull(grade_value) or grade_value == "NaT" or str(grade_value) == "nan":
            grade_value = "NaN"
        else:
            grade_value = f"{grade_value:.0f}"
        row_values.append(grade_value)

        row = "[" + ",".join(map(str, row_values)) + "]"
        chart_rows.append(row + "\n")
    chart_data = ",".join(chart_rows)

    download_url = (
        f"/api/well_best_available_logger_data"
        f"?unit_hyphen={well.unit_hyphen}"
        f"&param={param}"
        f"&freq={freq}"
        f"&keep_grades={keep_grades_str}"
        f"&max_gap_days={int(max_gap_days)}"
        f"&start={start_str}"
        f"&finish={finish_str}"
        f"&aqts_env={aqts_env}"
        f"&format=csv"
    )

    dsets = gd.get_logger_interval_details(dfs)
    if len(dsets):
        dsets["csv_download"] = dsets.apply(
            lambda row: (
                f"<a href='"
                f"/api/well_best_available_logger_data"
                f"?unit_hyphen={well.unit_hyphen}"
                f"&param={param}"
                f"&freq={freq}"
                f"&keep_grades={keep_grades_str}"
                f"&max_gap_days={int(max_gap_days)}"
                f"&start={row.start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                f"&finish={row.finish_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                f"&aqts_env={aqts_env}"
                f"&format=csv"
                f"'>{row.dataset_length}-row CSV</a>"
            ),
            axis=1,
        )
    dsets_table = webapp_utils.frame_to_html(dsets)

    return templates.TemplateResponse(
        "well_logger_water_level.html",
        {
            "request": request,
            "env": env,
            "aqts_env": aqts_env,
            "title": format_well_title(well),
            "redirect_to": "well_logger_water_level",
            "singular_redirect_to": "well_logger_water_level",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "chart_data": chart_data,
            "start": start_str,
            "finish": finish_str,
            "freq": freq,
            "max_gap_days": max_gap_days,
            "param": param,
            "keep_grades": keep_grades_str,
            "dsets_table": dsets_table,
            "download_url": download_url,
            "trend_js": "",
            "trend_param": "",
        },
    )


@router.get("/well_combined_water_level")
def well_combined_water_level(
    request: Request,
    dh_no: int,
    param: str = "swl",
    keep_measured_during: str = "",
    freq: str = "1d",
    keep_grades: str = "1, 20, 30",
    max_gap_days: float = 550,
    start: str = "",
    finish: str = "",
    env: str = "prod",
    aqts_env: str = "prod",
) -> str:
    if not start:
        start = None
        start_str = ""
    else:
        start = gd.timestamp_acst(start)
        start_str = start.strftime("%Y-%m-%d")

    if not finish:
        finish = None
        finish_str = ""
    else:
        finish = gd.timestamp_acst(finish)
        finish_str = finish.strftime("%Y-%m-%d")

    keep_grades = [int(g) for g in keep_grades.split(",")] if keep_grades else []
    keep_grades_str = ", ".join([f"{g:.0f}" for g in sorted(keep_grades)])

    db = connect_to_sageodata(service_name=env)
    summ = db.wells_summary([dh_no])
    well = get_well_metadata(summ, dh_no)

    dfs = gd.get_combined_water_level_dataset(
        [well.dh_no],
        db=db,
        param=param,
        freq=freq,
        start=start,
        finish=finish,
        max_gap_days=max_gap_days,
        keep_grades=keep_grades,
        aq_env=aqts_env,
    )
    df = gd.join_logger_data_intervals(dfs)
    df = df.dropna(subset=[param], how="any")

    chart_rows = []
    for idx, record in df.iterrows():
        record = record.to_dict()
        record["js_date"] = record["timestamp"].strftime(f'new Date("%Y/%m/%d %H:%M")')
        row_values = [record["js_date"]]

        wl_value = record[param]
        if pd.isnull(wl_value) or wl_value == "NaT" or str(wl_value) == "nan":
            wl_value = "NaN"
        else:
            wl_value = f"{wl_value:.3f}"
        row_values.append(wl_value)

        grade_value = record["grade"]
        if pd.isnull(grade_value) or grade_value == "NaT" or str(grade_value) == "nan":
            grade_value = "NaN"
        else:
            grade_value = f"{grade_value:.0f}"
        row_values.append(grade_value)

        sagd_value = np.nan
        if record["database"] == "SAGD":
            sagd_value = record[param]
        if pd.isnull(sagd_value) or sagd_value == "NaT" or str(sagd_value) == "nan":
            sagd_value = "NaN"
        else:
            sagd_value = f"{sagd_value:.2f}"
        row_values.append(sagd_value)

        aqts_value = np.nan
        if record["database"] == "AQTS":
            aqts_value = record[param]
        if pd.isnull(aqts_value) or aqts_value == "NaT" or str(aqts_value) == "nan":
            aqts_value = "NaN"
        else:
            aqts_value = f"{aqts_value:.3f}"
        row_values.append(aqts_value)

        row = "[" + ",".join(map(str, row_values)) + "]"
        chart_rows.append(row + "\n")
    chart_data = ",".join(chart_rows)
    # for idx, record in df.iterrows():
    #     record = record.to_dict()
    #     row_str = "[ " + record["timestamp"].strftime(f'new Date("%Y/%m/%d %H:%M")')
    #     for column in chart_columns:
    #         value = record[column]
    #         if not str(value) in ("null", "NaN", "NaT"):
    #             if column.startswith("rswl"):
    #                 value = f"{value:.3f}"
    #             else:
    #                 value = f"{value * -1:.3f}"

    #         if value in ("NaT", "NaN", "nan"):
    #             value = "NaN"
    #         elif value == "null":
    #             # important to keep "null" - used by dygraphs
    #             pass
    #         else:
    #             # numerical value has been encoded.
    #             pass

    #         row_str += f", {value}"
    #     row_str += "]"
    #     chart_rows.append(row_str + "\n")
    # chart_data = ",".join(chart_rows)
    # chart_columns_str = ", ".join([f'"{col}"' for col in chart_columns])

    url_str = webapp_utils.dhnos_to_urlstr([dh_no])

    download_url = (
        f"/api/well_best_available_combined_water_level_data"
        f"?url_str={url_str}"
        f"&param={param}"
        f"&freq={freq}"
        f"&keep_grades={keep_grades_str}"
        f"&max_gap_days={int(max_gap_days)}"
        f"&start={start_str}"
        f"&finish={finish_str}"
        f"&env={env}"
        f"&aqts_env={aqts_env}"
        f"&format=csv"
    )
    dsets = gd.get_logger_interval_details(dfs)
    if len(dsets):
        dsets["csv_download"] = dsets.apply(
            lambda row: (
                f"<a href='"
                f"/api/well_best_available_combined_water_level_data"
                f"?url_str={url_str}"
                f"&param={param}"
                f"&freq={freq}"
                f"&keep_grades={keep_grades_str}"
                f"&max_gap_days={int(max_gap_days)}"
                f"&start={row.start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                f"&finish={row.finish_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                f"&env={env}"
                f"&aqts_env={aqts_env}"
                f"&format=csv"
                f"'>{row.dataset_length}-row CSV</a>"
            ),
            axis=1,
        )
    dsets_table = webapp_utils.frame_to_html(dsets)

    return templates.TemplateResponse(
        "well_combined_water_level.html",
        {
            "request": request,
            "env": env,
            "aqts_env": aqts_env,
            "title": format_well_title(well),
            "redirect_to": "well_combined_water_level",
            "singular_redirect_to": "well_combined_water_level",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": f"url_str={url_str}",
            "well": well,
            "chart_data": chart_data,
            "start": start_str,
            "finish": finish_str,
            "freq": freq,
            "max_gap_days": max_gap_days,
            "param": param,
            "keep_grades": keep_grades_str,
            "dsets_table": dsets_table,
            "download_url": download_url,
        },
    )


@router.get("/well_salinity")
def well_salinity(
    request: Request,
    dh_no: int,
    ignore_anomalous: bool = False,
    keep_measured_during: str = "",
    keep_extract_method: str = "",
    env: str = "prod",
) -> str:
    db = connect_to_sageodata(service_name=env)
    df = db.salinities([dh_no]).sort_values("collected_date", ascending=False)
    well = get_well_metadata(df, dh_no)
    df["charted"] = "Y"
    if ignore_anomalous:
        df.loc[df.anomalous_ind == "Y", "charted"] = "N - anomalous"
    if keep_measured_during:
        df.loc[
            ~df.measured_during.isin(keep_measured_during.upper().split(",")), "charted"
        ] = f"N - measured_during not in {keep_measured_during}"
    if keep_extract_method:
        df.loc[
            ~df.extract_method.isin(keep_extract_method.upper().split(",")), "charted"
        ] = f"N - measured_during not in {keep_extract_method}"

    table = webapp_utils.frame_to_html(
        gd.cleanup_columns(df, keep_cols=[]).drop(
            ["amg_easting", "amg_northing"], axis=1
        )
    )

    cols_for_record = [
        "js_date",
        "ec",
        "tds",
        "anomalous_ind",
        "measured_during",
        "extract_method",
        "depth_from",
        "comments",
    ]
    chart_rows = []
    for idx, record in (
        df[df.charted == "Y"]
        .dropna(subset=["ec", "collected_date", "tds"], how="any")
        .sort_values("collected_date")
        .iterrows()
    ):
        record = record.to_dict()
        record["js_date"] = record["collected_date"].strftime(
            f'new Date("%Y-%m-%dT%H:%M")'
        )
        row_values = [webapp_utils.fmt_for_js(record[col]) for col in cols_for_record]
        row = "[" + ", ".join(row_values) + "]"
        chart_rows.append(row)
    sal_js_dataset = ",\n ".join(chart_rows)

    return templates.TemplateResponse(
        "well_salinity.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_salinity",
            "singular_redirect_to": "well_salinity",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "df": df,
            "sal_js_dataset": sal_js_dataset,
            "table": table,
            "ignore_anomalous": ignore_anomalous,
            "keep_measured_during": keep_measured_during,
            "keep_extract_method": keep_extract_method,
        },
    )


@router.get("/well_drillhole_logs")
def well_drillhole_logs(request: Request, dh_no: int, env: str = "prod") -> str:
    db = connect_to_sageodata(service_name=env)

    logs = db.drillhole_logs([dh_no]).sort_values("log_date", ascending=True)
    log_types = logs.log_type.unique()

    drill = db.drillers_logs([dh_no]).sort_values(["depth_from", "depth_to"])
    lith = db.lith_logs([dh_no]).sort_values(["depth_from", "depth_to"])
    strat = db.strat_logs([dh_no]).sort_values(["depth_from", "depth_to"])
    hstrat = db.hydrostrat_logs([dh_no])

    drill = gd.add_elev_cols(drill, dh_no)
    lith = gd.add_elev_cols(lith, dh_no)
    strat = gd.add_elev_cols(strat, dh_no)
    hstrat = gd.add_elev_cols(hstrat, dh_no)

    if len(strat):
        strat["map_symbol"] = strat.map_symbol.apply(
            lambda m: f"<a href='/app/strat_units?map_symbol={m}&env={env}'>{m}</a>"
        )

    if len(hstrat):
        hstrat["unit_code"] = hstrat.unit_code.apply(
            lambda m: f"<a href='/app/strat_units?map_symbol={m}&env={env}'>{m}</a>"
        )
        hstrat["hyd_int_code"] = hstrat.hyd_int_code.apply(
            lambda m: f"<a href='/app/strat_units?map_symbol={m}&env={env}'>{m}</a>"
        )

    well = get_well_metadata(logs, dh_no)

    logs_table = webapp_utils.frame_to_html(gd.cleanup_columns(logs, keep_cols=[]))
    drill_table = webapp_utils.frame_to_html(gd.cleanup_columns(drill, keep_cols=[]))
    lith_table = webapp_utils.frame_to_html(gd.cleanup_columns(lith, keep_cols=[]))
    strat_table = webapp_utils.frame_to_html(gd.cleanup_columns(strat, keep_cols=[]))
    hstrat_table = webapp_utils.frame_to_html(gd.cleanup_columns(hstrat, keep_cols=[]))

    return templates.TemplateResponse(
        "well_drillhole_logs.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_drillhole_logs",
            "singular_redirect_to": "well_drillhole_logs",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "logs": logs,
            "log_types": log_types,
            "drill": drill,
            "lith": lith,
            "strat": strat,
            "hstrat": hstrat,
            "logs_table": logs_table,
            "drill_table": drill_table,
            "lith_table": lith_table,
            "strat_table": strat_table,
            "hstrat_table": hstrat_table,
        },
    )


@router.get("/well_construction")
def well_construction(request: Request, dh_no: int, env: str = "prod") -> str:
    db = connect_to_sageodata(service_name=env)

    cevents_df = db.construction_events([dh_no]).sort_values(
        "completion_date", ascending=False
    )

    well = get_well_metadata(cevents_df, dh_no)

    cevents_df = gd.add_construction_activity_column(cevents_df)
    cevents_df["auto_dwcr"] = cevents_df.apply(
        lambda row: (
            f"<a href='/api/well_auto_dwcr?dh_no={row.dh_no}&completion_no={row.completion_no}&env={env}'>Auto DWCR</a>"
            if row.event_type == "C"
            else ""
        ),
        axis=1,
    )

    summary_cols = [
        "completion_date",
        "event_type",
        "activity",
        "wcr_id",
        "auto_dwcr",
        "driller_name",
        "driller_class",
        "permit_no",
        "comments",
        "total_depth",
        "final_depth",
        "current_depth",
        "final_swl",
        "final_yield",
        "drill_method",
        "drill_to",
        "casing_material",
        "casing_min_diam",
        "casing_to",
        "pzone_type",
        "pzone_material",
        "pzone_diam",
        "pzone_from",
        "pzone_to",
    ]

    cevents_df_for_table = cevents_df.copy()
    cevents_df_for_table["permit_no"] = cevents_df_for_table.permit_no.apply(
        lambda pn: (
            f"<a href='/app/permit?permit_no={pn}&env={env}'>{pn}</a>" if pn else ""
        )
    )
    summary_table = webapp_utils.frame_to_html(
        gd.cleanup_columns(cevents_df_for_table[summary_cols], keep_cols=[])
    )

    # drilling, casing, wcuts, pzones, other_items
    drilling = db.drilled_intervals([dh_no]).sort_values(["depth_from", "depth_to"])
    casing = db.casing_strings([dh_no]).sort_values(["depth_from", "depth_to"])
    seals = db.casing_seals([dh_no]).sort_values("seal_depth")
    wcuts = db.water_cuts([dh_no]).sort_values(["depth_from", "depth_to"])
    pzones = db.production_zones([dh_no]).sort_values(["depth_from", "depth_to"])
    other_items = db.other_construction_items([dh_no]).sort_values(
        ["depth_from", "depth_to"]
    )

    elev = (
        db.elevation_surveys([dh_no])
        .pipe(gd.cleanup_columns)
        .assign(**{"ref_height [calculated]": pd.NA})
    )
    elev.loc[
        (~pd.isnull(elev.ground_elev)) & (~pd.isnull(elev.ref_elev)),
        "ref_height [calculated]",
    ] = (
        elev.ref_elev - elev.ground_elev
    )
    elev_cols = [
        "elev_date",
        "applied_date",
        "ground_elev",
        "ref_elev",
        "ref_height [calculated]",
        "survey_meth",
        "ref_point_type",
        "comments",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    elev = elev[elev_cols]

    cevents = []
    sevents = []

    kws = dict(
        keep_cols=[],
        drop=("construction_aquifer", "completion_no", "completion_date", "event_type"),
    )

    for completion_no, cevent_summ in cevents_df.groupby("completion_no"):
        summary = gd.cleanup_columns(cevent_summ, keep_cols=[]).iloc[0]
        if summary.event_type == "C":
            title = f"Construction event "
        elif summary.event_type == "S":
            title = f"Survey event "
        title += webapp_utils.format_datetime(summary.completion_date)

        pn = str(summary.permit_no)
        summary["permit_no"] = (
            f"<a href='/app/permit?permit_no={pn}&env={env}'>{pn}</a>" if pn else ""
        )
        summary["permit_no_full"] = (
            f"<a href='/app/permit?permit_no={pn}&env={env}'>{summary.permit_no_full}</a>"
            if pn
            else ""
        )

        summary = summary.drop(
            [
                "latest",
                "max_case",
                "orig_case",
                "lod_case",
                "from_flag",
            ]
        )
        summary_1_cols = [
            "commenced_date",
            "completion_date",
            "completion_no",
            "event_type",
            "activity",
            "wcr_id",
            "auto_dwcr",
            "permit_no_full",
            "driller_name",
            "driller_class",
            "plant_operator",
            "construction_aquifer",
            "total_depth",
            "final_depth",
            "current_depth",
            # "start_depth",
        ]
        summary_2_cols = [
            "drill_method",
            "drill_from",
            "drill_to",
            "drill_diam",
            "casing_material",
            "casing_from",
            "casing_to",
            "casing_diam",
            "casing_min_diam",
            "pzone_type",
            "pzone_material",
            "pzone_from",
            "pzone_to",
            "pzone_diam",
            "pcement_from",
            "pcement_to",
            "created_by",
            "creation_date",
            "modified_by",
            "modified_date",
        ]

        summary_1 = summary[summary_1_cols]
        summary_2 = summary[summary_2_cols]
        summary_12 = summary[summary_1_cols + summary_2_cols]

        cevent = {
            "data_types": [],
            "title": title,
            "summary": summary,
            "summary_1": summary_1,
            "summary_2": summary_2,
            "summary_12": summary_12,
            "comments": summary.comments,
            "summary_table": webapp_utils.series_to_html(
                summary.drop(index=["comments"]), transpose=False
            ),
            "summary_1_table": webapp_utils.series_to_html(summary_1, transpose=False),
            "summary_2_table": webapp_utils.series_to_html(summary_2, transpose=False),
            "summary_12_table": webapp_utils.series_to_html(summary_12, transpose=True),
        }

        cevent_drilling = drilling[drilling.completion_no == completion_no]
        cevent_casing = casing[casing.completion_no == completion_no]
        cevent_seals = seals[seals.completion_no == completion_no]
        cevent_wcuts = wcuts[wcuts.completion_no == completion_no]
        cevent_pzones = pzones[pzones.completion_no == completion_no]
        cevent_other_items = other_items[other_items.completion_no == completion_no]

        cevent_drilling = gd.add_elev_cols(cevent_drilling, dh_no)
        cevent_casing = gd.add_elev_cols(cevent_casing, dh_no)
        cevent_seals = gd.add_elev_cols(cevent_seals, dh_no)
        cevent_wcuts = gd.add_elev_cols(cevent_wcuts, dh_no)
        cevent_pzones = gd.add_elev_cols(cevent_pzones, dh_no)
        cevent_other_items = gd.add_elev_cols(cevent_other_items, dh_no)

        if len(cevent_drilling) > 0:
            cevent["drilling"] = webapp_utils.frame_to_html(
                gd.cleanup_columns(cevent_drilling, **kws)
            )
            cevent["data_types"].append("drilling")

        if len(cevent_casing) > 0:
            cevent["casing"] = webapp_utils.frame_to_html(
                gd.cleanup_columns(cevent_casing, **kws)
            )
            cevent["data_types"].append("casing")

        if len(cevent_seals) > 0:
            cevent["seals"] = webapp_utils.frame_to_html(
                gd.cleanup_columns(cevent_seals, **kws)
            )
            cevent["data_types"].append("seals")

        if len(cevent_wcuts) > 0:
            cevent["wcuts"] = webapp_utils.frame_to_html(
                gd.cleanup_columns(cevent_wcuts, **kws)
            )
            cevent["data_types"].append("wcuts")

        if len(cevent_pzones) > 0:
            drop_cols = [
                c for c in ["pzone_from", "pzone_to"] if c in cevent_pzones.columns
            ]
            cevent["pzones"] = webapp_utils.frame_to_html(
                gd.cleanup_columns(cevent_pzones.drop(drop_cols, axis=1), **kws)
            )
            cevent["data_types"].append("pzones")

        if len(cevent_other_items) > 0:
            cevent["other_items"] = webapp_utils.frame_to_html(
                gd.cleanup_columns(cevent_other_items, **kws)
            )
            cevent["data_types"].append("other_items")

        if summary.event_type == "C":
            cevents.append(cevent)
        elif summary.event_type == "S":
            sevents.append(cevent)

    cevents = sorted(cevents, key=lambda x: x["summary"].completion_date)
    sevents = sorted(sevents, key=lambda x: x["summary"].completion_date)
    elev_table = webapp_utils.frame_to_html(elev)

    return templates.TemplateResponse(
        "well_construction.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_construction",
            "singular_redirect_to": "well_construction",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "summary_table": summary_table,
            "events": [cevents, sevents],
            "elev": elev,
            "elev_table": elev_table,
        },
    )


@router.get("/well_drillhole_document_images")
def well_drillhole_document_images(
    request: Request,
    dh_no: int,
    env: str = "prod",
    width: int = 950,
    height: int = -1,
    inline: bool = True,
    new_tab: bool = True,
) -> str:
    db = connect_to_sageodata(service_name=env)
    df = db.drillhole_document_image_list([dh_no])
    well = get_well_metadata(df, dh_no)

    images = []
    for idx, image in df.iterrows():
        m = re.search(r"rotate_(c?cw)_([0-9]+)", str(image.comments))
        rotation = 0
        if m:
            rotation = int(m.group(2))
            if m.group(1) == "ccw":
                rotation *= -1
        image["rotation"] = rotation
        images.append(image)

    return templates.TemplateResponse(
        "well_drillhole_document_images.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_drillhole_document_images",
            "singular_redirect_to": "well_drillhole_document_images",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "df": df,
            "images": images,
            "width": width,
            "height": height,
            "inline": inline,
            "new_tab": new_tab,
            "target": "_blank" if new_tab else "",
        },
    )


@router.get("/well_drillhole_images")
def well_drillhole_images(
    request: Request,
    dh_no: int,
    env: str = "prod",
    width: int = 400,
    height: int = -1,
    inline: bool = True,
    new_tab: bool = True,
) -> str:
    db = connect_to_sageodata(service_name=env)
    df = db.drillhole_image_list([dh_no])
    df = df.sort_values("image_date")

    images = []
    for idx, row in df.iterrows():
        im = row.to_dict()
        im["pretty_date"] = "NA"
        if not pd.isnull(row.image_date):
            im["pretty_date"] = row.image_date.strftime("%d/%m/%Y")
        for field in ["photographer", "title", "direction"]:
            if not im[field]:
                im[field] = ""
        images.append(im)

    well = get_well_metadata(df, dh_no)

    return templates.TemplateResponse(
        "well_drillhole_images.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_drillhole_images",
            "singular_redirect_to": "well_drillhole_images",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "df": df,
            "images": images,
            "width": width,
            "height": height,
            "inline": inline,
            "new_tab": new_tab,
            "target": "_blank" if new_tab else "",
        },
    )


@router.get("/well_geophysical_logs")
def well_geophysical_logs(
    request: Request,
    dh_no: int,
    env: str = "prod",
) -> str:
    db = connect_to_sageodata(service_name=env)
    md = db.geophys_log_metadata([dh_no])
    job_nos = md.job_no.unique()
    files = gd.list_geophys_job_files(job_nos=job_nos, add_las_metadata=True)
    well = get_well_metadata(md, dh_no)

    md_lookup = md.set_index("job_no").logged_date
    files.insert(1, "logged_date", files.job_no.map(md_lookup))

    files_tables = []
    job_row_cols = [
        "log_hdr_no",
        "project",
        "client",
        "location",
        "purpose",
        "operators",
        "vehicle",
        "gl_dh_name",
        "gl_permit_no",
        "max_log_depth",
        "comments",
    ]

    def link_log_types(row):
        log_types = [lt.strip() for lt in row.log_types.split(",")]
        links = []
        for log_type in log_types:
            links.append(
                f"<a href='/app/well_geophysical_log_las_file?job_no={row.job_no}&filename={row.filename}&log_type={log_type}'>{log_type}</a>"
            )
        links.append(
            f"<a href='/app/well_geophysical_log_las_file?job_no={row.job_no}&filename={row.filename}'>[all log type curves]</a>"
        )
        return ", ".join(links)

    def link_log_mnemonics(row):
        mnemonics = [m.strip() for m in row.mnemonics.split(",")]
        links = []
        for mnemonic in mnemonics:
            links.append(
                f"<a href='/app/well_geophysical_log_las_file?job_no={row.job_no}&filename={urllib.parse.quote(row.filename)}&mnemonic={mnemonic}'>{mnemonic}</a>"
            )
        links.append(
            f"<a href='/app/well_geophysical_log_las_file?job_no={row.job_no}&filename={urllib.parse.quote(row.filename)}'>[all curves]</a>"
        )
        return ", ".join(links)

    files_cols = [
        "logged_date",
        "job_no",
        "filename",
        "file_type",
        "file_size",
        "csv_download",
        "max_depth_las",
        "log_types",
        "mnemonics",
    ]

    for (logged_date, job_no), job_files in files.groupby(
        ["logged_date", "job_no"], as_index=False
    ):
        job_files.loc[job_files.file_type == "LAS", "log_types"] = job_files.apply(
            link_log_types, axis=1
        )
        job_files.loc[job_files.file_type == "LAS", "mnemonics"] = job_files.apply(
            link_log_mnemonics, axis=1
        )
        img = '<img src="/static/download.svg" width="14px" height="14px" />'
        job_files.loc[job_files.file_type == "LAS", "csv_download"] = job_files.apply(
            lambda row: f"<a href='/api/well_geophysical_las_file_data?job_no={row.job_no}&filename={urllib.parse.quote(row.filename)}'>{img}</a>",
            axis=1,
        )
        job_files["filename"] = job_files.filename.apply(
            lambda filename: f"<a href='/api/well_geophysical_log_file?job_no={job_no}&filename={urllib.parse.quote(filename)}'>{filename}</a>"
        )
        files_table = webapp_utils.frame_to_html(
            gd.cleanup_columns(job_files[files_cols], drop=["path"], keep_cols=[])
        )
        md_row_table = webapp_utils.series_to_html(
            md.loc[md.job_no == job_no, job_row_cols].iloc[0],
            transpose=False,
        )

        files_tables.append(
            [job_no, logged_date.strftime("%d/%m/%Y"), md_row_table, files_table]
        )

    md["job_no"] = md.job_no.apply(lambda j: f"<a href='#{j}'>{j}</a>")

    md_cols = [
        "job_no",
        "log_hdr_no",
        "logged_date",
        "project",
        "client",
        "location",
        "purpose",
        "operators",
        "vehicle",
        "max_log_depth",
        "comments",
    ]
    md_table = webapp_utils.frame_to_html(gd.cleanup_columns(md, keep_cols=[])[md_cols])

    return templates.TemplateResponse(
        "well_geophysical_logs.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_geophysical_logs",
            "singular_redirect_to": "well_geophysical_logs",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "md": md,
            "files": files,
            "md_table": md_table,
            "files_tables": files_tables,
        },
    )


@router.get("/well_geophysical_log_las_file")
def well_geophysical_log_las_file(
    request: Request,
    job_no: int,
    filename: str,
    log_type: str = "",
    mnemonic: str = "",
    env: str = "prod",
) -> str:
    db = connect_to_sageodata(service_name=env)
    job_path = gd.find_job_folder(job_no)
    file_path = job_path / filename

    md = db.geophys_log_metadata_by_job_no([job_no])
    dh_no = md.dh_no.iloc[0]
    well = get_well_metadata(md, dh_no)

    las = lasio.read(file_path)
    las_md = gd.get_las_metadata(las=las)

    if log_type:
        include_mnemonics = [
            m["las_mnemonic"] for m in las_md["mnemonics"] if m["log_type"] == log_type
        ]
    elif mnemonic:
        include_mnemonics = [
            m["las_mnemonic"]
            for m in las_md["mnemonics"]
            if m["las_mnemonic"] == mnemonic
        ]
    else:
        include_mnemonics = [
            m["las_mnemonic"] for m in las_md["mnemonics"] if m["log_type"] != "?"
        ]
    graph = pozo.Graph(las, include=include_mnemonics)

    fig_html = graph.render(height=750).to_html(full_html=False, include_plotlyjs=True)

    if dh_no:
        wells_query_params = "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no])
    else:
        wells_query_params = ""

    return templates.TemplateResponse(
        "well_geophysical_log_las_file.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_geophysical_logs",
            "singular_redirect_to": "well_geophysical_logs",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": wells_query_params,
            "well": well,
            "fig_html": fig_html,
        },
    )


@router.get("/well_extraction_injection")
def extraction_injection(request: Request, dh_no: int, env: str = "prod") -> str:
    db = connect_to_sageodata(service_name=env)
    df = db.drillhole_details([dh_no])
    well = get_well_metadata(df, dh_no)

    wdb = gd.connect_to_package_database()
    usage = pd.read_sql(
        f"select * from usage where unit_hyphen = '{well.unit_hyphen}' and month is null",
        wdb,
    )
    usage = usage.sort_values(["calendar_year", "financial_year"])
    if len(usage.calendar_year.dropna()) > len(usage.financial_year.dropna()):
        usage_year_col = "calendar_year"
    else:
        usage_year_col = "financial_year"

    cols_for_record = ["js_date", "effective_kl"]
    chart_rows = []
    for idx, record in usage.iterrows():
        record = record.to_dict()
        record["js_date"] = record[usage_year_col]
        row_values = [webapp_utils.fmt_for_js(record[col]) for col in cols_for_record]
        row = "[" + ", ".join(row_values) + "]"
        chart_rows.append(row)
    usage_js_dataset = ",\n ".join(chart_rows)

    usage_table = webapp_utils.frame_to_html(usage)

    return templates.TemplateResponse(
        "well_extraction_injection.html",
        {
            "request": request,
            "env": env,
            "title": format_well_title(well),
            "redirect_to": "well_drillhole_logs",
            "singular_redirect_to": "well_extraction_injection",
            "plural_redirect_to": "wells_summary",
            "wells_title": "1 well",
            "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            "well": well,
            "usage": usage,
            "usage_table": usage_table,
            "usage_js_dataset": usage_js_dataset,
            "usage_year_col": usage_year_col,
        },
    )
