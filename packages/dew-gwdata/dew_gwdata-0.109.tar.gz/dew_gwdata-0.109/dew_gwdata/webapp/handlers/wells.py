from pathlib import Path
from typing import Annotated
import logging

import pandas as pd
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sageodata_db import connect as connect_to_sageodata
from sageodata_db import load_predefined_query
from sageodata_db.utils import parse_query_metadata

import dew_gwdata as gd

from dew_gwdata.webapp import utils as webapp_utils
from dew_gwdata.webapp import query_models


router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


logger = logging.getLogger(__name__)


def run_wells_query(conn, query_name, args):
    if len(args):
        return getattr(conn, query_name)(args)
    else:
        cols, _, _ = parse_query_metadata(load_predefined_query(query_name))
        return pd.DataFrame(columns=cols)


def process_wells_result(conn, dh_nos):
    if len(dh_nos):
        gl = conn.geophys_log_metadata(dh_nos).dropna(subset=["job_no"])
        jobstr = webapp_utils.dhnos_to_urlstr(gl.job_no.unique())
    else:
        jobstr = ""
    return {"jobstr": jobstr}


@router.get("/wells_summary")
def wells_summary(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)

    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    df = run_wells_query(db, "wells_summary", dh_nos)

    # Would be much better to apply the arbitrary order from *wells* into *df* than this method.
    df = df.sort_values(
        [query.sort], ascending=True if query.order.startswith("asc") else False
    )
    final_cols = [
        "latest_status",
        "latest_swl",
        "latest_tds",
        "purpose",
        "owner",
        "orig_drilled_depth",
        "orig_drilled_date",
        "latest_cased_to",
        "comments",
    ]

    df_for_table = webapp_utils.prep_table_for_html(df, cols=final_cols, query=query)
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in df.dh_no]) + ")"
    )

    return templates.TemplateResponse(
        "wells_summary.html",
        {
            "request": request,
            "env": query.env,
            "title": title,
            "query": query,
            "redirect_to": "wells_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "wells_title": title,
            "wells_query_params": query_params,
            "wells": df,
            "wells_table": table,
            "egis_layer_definition_query": egis_layer_definition_query,
            "result": result,
        },
    )


@router.get("/wells_ownership_status")
def wells_ownership_status(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)
    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    df = run_wells_query(db, "wells_summary", dh_nos)

    df = df.sort_values(
        [query.sort], ascending=True if query.order.startswith("asc") else False
    )

    final_cols = [
        "orig_drilled_depth",
        "orig_drilled_date",
        "purpose",
        "latest_status",
        "owner",
        "state_asset",
        "state_asset_status",
        "state_asset_retained",
        "state_asset_comments",
        "comments",
    ]
    df_for_table = webapp_utils.prep_table_for_html(df, cols=final_cols, query=query)
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in df.dh_no]) + ")"
    )

    return templates.TemplateResponse(
        "wells_ownership_status.html",
        {
            "request": request,
            "env": query.env,
            "title": title,
            "query": query,
            "redirect_to": "wells_ownership_status",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_ownership_status",
            "wells_title": title,
            "wells_query_params": query_params,
            "wells": df,
            "wells_table": table,
            "egis_layer_definition_query": egis_layer_definition_query,
            "result": result,
        },
    )


@router.get("/wells_data_available")
def wells_data_available(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)
    wells, name, name_safe, query_params = query.find_wells()

    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    summ = run_wells_query(db, "wells_summary", dh_nos)
    data = run_wells_query(db, "data_available", dh_nos)

    summ = summ.sort_values(
        [query.sort], ascending=True if query.order.startswith("asc") else False
    )

    col_to_endpoint_map = {
        "drill_or_lith_logs": "well_drillhole_logs",
        "strat_or_hydro_logs": "well_drillhole_logs",
        "water_levels": "well_manual_water_level",
        "elev_surveys": "well_summary",
        "aquarius_flag": "well_combined_water_level",
        "salinities": "well_salinity",
        "water_cuts": "well_construction",
        "geophys_logs": "well_geophysical_logs",
        "dh_docimg_flag": "well_drillhole_document_images",
        "photo_flag": "well_drillhole_images",
    }
    for col, endpoint in col_to_endpoint_map.items():
        data[col] = data.apply(
            lambda row: (
                f'<a href="/app/{endpoint}?dh_no={row.dh_no}&env={query.env}">{row[col]}</a>'
                if row[col] > 0
                else 0
            ),
            axis=1,
        )

    summ["orig_drilled_depth"] = summ.orig_drilled_depth.apply(
        lambda v: f"{v:.02f}" if not pd.isnull(v) else ""
    )
    df = pd.merge(summ, data, on="dh_no")
    summ_final_cols = [
        "orig_drilled_depth",
        "orig_drilled_date",
    ]
    summ_final_cols += [k for k in col_to_endpoint_map.keys()]
    df_for_table = webapp_utils.prep_table_for_html(
        df, cols=summ_final_cols, query=query
    )

    def series_styler(series):
        def value_function(value):
            if value == 0:
                return "border: 1px solid grey;"
            else:
                return "background-color: lightgreen; border: 1px solid grey;"

        return series.apply(value_function)

    apply_colours_to = [
        c
        for c in df_for_table.columns
        if not c in summ.columns and not c in ("title", "suburb")
    ]

    table = webapp_utils.frame_to_html(
        df_for_table,
        apply=series_styler,
        apply_kws=dict(
            axis=1,
            subset=apply_colours_to,
        ),
    )

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in summ.dh_no]) + ")"
    )

    return templates.TemplateResponse(
        "wells_data_available.html",
        {
            "request": request,
            "env": query.env,
            "title": title,
            "query": query,
            "redirect_to": "wells_data_available",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_data_available",
            "wells_title": title,
            "wells_query_params": query_params,
            "wells": summ,
            "wells_table": table,
            "egis_layer_definition_query": egis_layer_definition_query,
            "result": result,
        },
    )


@router.get("/wells_driller_info")
def wells_driller_info(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)

    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    summ = run_wells_query(db, "wells_summary", dh_nos)

    summ = summ.sort_values(
        [query.sort], ascending=True if query.order.startswith("asc") else False
    )
    const = db.construction_events(dh_nos)
    const = const[const.event_type == "C"]
    gd.add_construction_activity_column(const)

    const["permit_no"] = const.permit_no.apply(
        lambda pn: (
            f"<a href='/app/permit?permit_no={pn}&env={query.env}'>{pn}</a>"
            if pn
            else ""
        )
    )
    const["auto_dwcr"] = const.apply(
        lambda row: f"<a href='/api/well_auto_dwcr?dh_no={row.dh_no}&completion_no={row.completion_no}&env={query.env}'>Auto DWCR</a>",
        axis=1,
    )
    const["construction_comment"] = const["comments"]

    def format_date(x):
        if x is None:
            return "[missing]"
        else:
            return pd.Timestamp(x).strftime("%d/%m/%Y")

    df_for_table = pd.merge(summ, const, on="dh_no", how="left", suffixes=(None, "_y"))
    df_for_table.loc[
        df_for_table.completion_date.notnull(), "completion_date"
    ] = df_for_table.loc[df_for_table.completion_date.notnull()].apply(
        lambda row: f'<a href="/app/well_construction?dh_no={row.dh_no}">{format_date(row.completion_date)}</a>',
        axis=1,
    )
    final_cols = [
        "latest_tds",
        "purpose",
        "completion_date",
        "orig_flag",
        "activity",
        "wcr_id",
        "auto_dwcr",
        "permit_no",
        "driller_name",
        "total_depth",
        "construction_comment",
    ]
    df_for_table = webapp_utils.prep_table_for_html(
        df_for_table,
        cols=final_cols,
        set_index=["latest_tds", "purpose", "completion_date"],
        query=query,
    )
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in dh_nos]) + ")"
    )

    return templates.TemplateResponse(
        "wells_driller_info.html",
        {
            "request": request,
            "env": query.env,
            "title": title,
            "query": query,
            "redirect_to": "wells_driller_info",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_driller_info",
            "wells_title": title,
            "wells_query_params": query_params,
            "wells": summ,
            "wells_table": table,
            "egis_layer_definition_query": egis_layer_definition_query,
            "result": result,
        },
    )


@router.get("/wells_in_group")
def wells_in_group(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    query.group_code = query.group_code.upper()
    db = connect_to_sageodata(service_name=query.env)

    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    groups = db.group_details()
    if not query.group_code in groups.group_code.unique():
        return RedirectResponse(
            f"/app/wells_summary?{query_params}&error_message=Group code must be specified - please search or filter for group in the query form above."
        )
    group = groups[groups.group_code == query.group_code].iloc[0]
    dhs = run_wells_query(db, "wells_in_groups", [query.group_code])
    dhs = dhs[dhs.dh_no.isin(dh_nos)]

    dhs["dh_comments"] = dhs.dh_comments.fillna("")

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in dh_nos]) + ")"
    )

    final_cols = [
        "swl_status",
        "swl_freq",
        "tds_status",
        "tds_freq",
        "dh_comments",
        "dh_created_by",
        "dh_creation_date",
        "dh_modified_by",
        "dh_modified_date",
    ]

    df_for_table = webapp_utils.prep_table_for_html(dhs, cols=final_cols, query=query)
    dhs_table = webapp_utils.frame_to_html(df_for_table)

    return templates.TemplateResponse(
        "wells_group_membership.html",
        {
            "request": request,
            "env": query.env,
            "redirect_to": "wells_in_group",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_in_group",
            "query": query,
            "wells": dhs,
            "wells_title": title,
            "wells_query_params": query_params,
            "group": group,
            "dhs": dhs,
            "wells_table": dhs_table,
            "group_code": query.group_code,
            "swl_status": query.swl_status,
            "tds_status": query.tds_status,
            "swl_freq": query.swl_freq,
            "tds_freq": query.tds_freq,
            "filter_group_comment": query.filter_group_comment,
            "result": result,
            "egis_layer_definition_query": egis_layer_definition_query,
        },
    )


@router.get("/wells_drillhole_logs")
def wells_drillhole_logs(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)

    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    logs = db.drillhole_logs(dh_nos)

    def get_map(log_type, logs_df):
        df = logs_df.copy()
        df["_label"] = df.apply(
            lambda row: (
                f"<a href='/app/well_drillhole_logs?dh_no={row.dh_no}&env={query.env}'>"
                f"{row.logged_by_name} {row.log_date.strftime('%d/%m/%Y')}</a> "
                f"{'<br />' + row.comments if row.comments else ''}"
            ),
            axis=1,
        )
        map_dict = df[df.log_type == log_type].set_index("dh_no")._label.to_dict()
        return map_dict

    for log_type_name in ("drillers_log", "lith_log", "strat_log", "hydrostrat_log"):
        log_type = log_type_name[0].upper()
        mapping = get_map(log_type, logs)
        wells[log_type_name] = wells.dh_no.apply(lambda dh_no: mapping.get(dh_no, ""))

    final_cols = [
        "max_drilled_depth",
        "orig_drilled_date",
        "drillers_log",
        "lith_log",
        "strat_log",
        "hydrostrat_log",
    ]

    df_for_table = webapp_utils.prep_table_for_html(wells, cols=final_cols, query=query)
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in dh_nos]) + ")"
    )

    return templates.TemplateResponse(
        "wells_drillhole_logs.html",
        {
            "request": request,
            "env": query.env,
            "redirect_to": "wells_drillhole_logs",
            "singular_redirect_to": "well_drillhole_logs",
            "plural_redirect_to": "wells_drillhole_logs",
            "query": query,
            "wells_title": title,
            "wells_query_params": query_params,
            "result": result,
            "table": table,
            "wells": wells,
            "dhs": wells,
            "egis_layer_definition_query": egis_layer_definition_query,
        },
    )


@router.get("/wells_aquifer_mon")
def wells_aquifer_mon(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)

    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    cols = [
        "aquifer_mon_from",
        "aquifer_mon",
        "aquifer_desc",
        "comments",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    additional_index_cols = ["aquifer_mon", "aquifer_mon_from", "aquifer_desc"]
    wells = db.wells_summary(dh_nos)
    aqmon = db.aquifers_monitored(dh_nos)
    aqmon = aqmon.rename(columns={"current_aquifer": "aquifer"})

    nonduplicate_cols = [c for c in aqmon.columns if not c in wells or c == "dh_no"]
    df = pd.merge(wells, aqmon[nonduplicate_cols], on="dh_no", how="left")

    df_for_table = webapp_utils.prep_table_for_html(
        df, cols=cols, set_index=additional_index_cols, query=query
    )
    df_for_table = df_for_table.fillna(
        " "
    )  # using ' ' instead of '' because of NaT bug https://github.com/pandas-dev/pandas/issues/11953
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in dh_nos]) + ")"
    )

    return templates.TemplateResponse(
        "wells_aquifer_mon.html",
        {
            "request": request,
            "env": query.env,
            "redirect_to": "wells_aquifer_mon",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_aquifer_mon",
            "query": query,
            "wells_title": title,
            "wells_query_params": query_params,
            "result": result,
            "table": table,
            "wells": aqmon,
            "dhs": aqmon,
            "egis_layer_definition_query": egis_layer_definition_query,
        },
    )


@router.get("/wells_salinity")
def wells_salinity(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
    ignore_anomalous: bool = False,
    keep_measured_during: str = "",
    keep_extract_method: str = "",
    param: str = "tds",
):
    db = connect_to_sageodata(service_name=query.env)

    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    df = db.salinities(dh_nos)

    def process_group(all_records):
        without_date = all_records[pd.isnull(all_records.collected_date)]
        df = all_records[~pd.isnull(all_records.collected_date)]
        df = df.sort_values("collected_date")
        if len(df):
            latest = df.iloc[-1].to_dict()
            mean_ec = df["ec"].dropna().mean()
            mean_tds = df["tds"].dropna().mean()
        else:
            latest = {}
        return pd.Series(
            {
                "n_records": len(df),
                "mean_ec": f"{mean_ec:.0f}" if mean_ec else "",
                "mean_tds": f"{mean_tds:.0f}" if mean_ec else "",
                "latest_date": latest.get("collected_date", ""),
                "latest_ec": latest.get("ec", ""),
                "latest_tds": latest.get("tds", ""),
                "latest_depth_from": latest.get("depth_from", ""),
                "latest_extract_method": latest.get("extract_method", ""),
                "latest_anomalous_ind": latest.get("anomalous_ind", ""),
                "latest_comment": latest.get("comments", ""),
            }
        ).fillna("")

    logger.debug(f"length df = {len(df)}")
    if len(df):
        df2 = df.groupby("dh_no").apply(process_group).reset_index()
    else:
        df2 = pd.DataFrame(
            columns=[
                "dh_no",
                "n_records",
                "mean_ec",
                "mean_tds",
                "latest_date",
                "latest_ec",
                "latest_tds",
                "latest_depth_from",
                "latest_extract_method",
                "latest_anomalous_ind",
                "comments",
            ]
        )

    df3 = pd.merge(
        wells[["dh_no", "obs_no", "unit_hyphen", "dh_name", "aquifer"]],
        df2,
        on="dh_no",
        how="left",
    )
    df3["n_records"] = df3.apply(
        lambda row: f"<a href='/app/well_salinity?dh_no={row.dh_no}&env={query.env}'>{row.n_records}</a>",
        axis=1,
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
    df["title"] = df.apply(lambda row: webapp_utils.make_dh_title(row), axis=1)
    if ignore_anomalous:
        df = df[~(df.anomalous_ind == "Y")]
    if keep_measured_during:
        measured_during = [m.upper().strip() for m in keep_measured_during.split(",")]
        df = df[df.measured_during.isin(measured_during)]
    if keep_extract_method:
        extract_method = [e.upper().strip() for e in keep_extract_method.split(",")]
        df = df[df.extract_method.isin(extract_method)]
    chart_contents = {}
    js_datasets_spec = []
    series_specs = []
    for i, (well_title, dfg) in enumerate(df.groupby("title")):
        well_chart_rows = []
        for idx, record in (
            dfg.dropna(subset=["ec", "collected_date", "tds"], how="any")
            .sort_values("collected_date")
            .iterrows()
        ):
            record = record.to_dict()
            if "\n" in str(record["comments"]):
                record["comments"] = record["comments"].replace("\n", " / ")
            record["js_date"] = record["collected_date"].strftime(
                f'new Date("%Y-%m-%dT%H:%M")'
            )
            row_values = [f'"{well_title}"']
            row_values += [
                webapp_utils.fmt_for_js(record[col]) for col in cols_for_record
            ]
            row = "[" + ", ".join(row_values) + "]"
            well_chart_rows.append(row)
        chart_contents[well_title] = ",\n".join(well_chart_rows)
        js_datasets_spec.append(
            f"source: salData['{well_title}'], dimensions: salDataCols"
        )
        series_specs.append(
            """
            {
                name: TEMPLATE_NAME,
                type: 'line',
                symbol: 'circle',
                symbolSize: 8,
                datasetIndex: TEMPLATE_INDEX,
                encode: {
                    x: 'collected_date',
                    y: 'TEMPLATE_PARAM',
                }
            }
        """.replace(
                "TEMPLATE_NAME", f"'{well_title}'"
            )
            .replace("TEMPLATE_INDEX", f"{i:.0f}")
            .replace("TEMPLATE_PARAM", f"{param}")
        )
    sal_js_dataset = (
        "{\n" + ",\n".join([f'"{t}": [{c}]' for t, c in chart_contents.items()]) + "}"
    )
    sal_js_datasets_spec = (
        "[" + ",\n".join(["{" + r + "}" for r in js_datasets_spec]) + "]"
    )
    sal_js_series_spec = ",\n".join(series_specs)

    main_cols = [c for c in df2.columns if not c == "dh_no"]

    cols = [
        "n_records",
        "mean_ec",
        "mean_tds",
        "latest_date",
        "latest_ec",
        "latest_tds",
        "latest_depth_from",
        "latest_extract_method",
        "latest_anomalous_ind",
        "latest_comment",
    ]

    df_for_table = webapp_utils.prep_table_for_html(df3, cols=cols, query=query)
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in dh_nos]) + ")"
    )

    return templates.TemplateResponse(
        "wells_salinity.html",
        {
            "request": request,
            "env": query.env,
            "redirect_to": "wells_salinity",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_salinity",
            "query": query,
            "wells_title": title,
            "wells_query_params": query_params,
            "result": result,
            "table": table,
            "wells": wells,
            "egis_layer_definition_query": egis_layer_definition_query,
            "sal_js_dataset": sal_js_dataset,
            "sal_js_datasets_spec": sal_js_datasets_spec,
            "sal_js_series_spec": sal_js_series_spec,
            "ignore_anomalous": ignore_anomalous,
            "keep_measured_during": keep_measured_during,
            "keep_extract_method": keep_extract_method,
            "param": param,
        },
    )


@router.get("/wells_water_level")
def wells_water_level(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
    aq_env: str = "prod",
):
    db = connect_to_sageodata(service_name=query.env)

    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    df = db.water_levels(dh_nos)

    def process_group(all_records):
        without_date = all_records[pd.isnull(all_records["obs_date"])]
        df = all_records[~pd.isnull(all_records["obs_date"])]
        df = df.sort_values("obs_date")
        if len(df):
            latest = df.iloc[-1].to_dict()
        else:
            latest = {}
        return pd.Series(
            {
                "n_records": len(df),
                # "mean_ec": f"{mean_ec:.0f}" if mean_ec else "",
                # "mean_tds": f"{mean_tds:.0f}" if mean_ec else "",
                "latest_obs_date": latest.get("obs_date", ""),
                "latest_dtw": latest.get("dtw", ""),
                "latest_swl": latest.get("swl", ""),
                "latest_rswl": latest.get("rswl", ""),
                "latest_anomalous_ind": latest.get("anomalous_ind", ""),
                "latest_comment": latest.get("comments", ""),
            }
        ).fillna("")

    aq = gd.DEWAquarius(env=aq_env)
    ts_df = aq.fetch_locations_timeseries_metadata(locids=df.unit_hyphen.unique())
    wl_ts_df = (
        ts_df[
            (ts_df.label == "Best Available")
            & (ts_df.param.isin(["Depth to Water", "SWL", "RSWL"]))
        ]
        .groupby("loc_id")
        .corr_end_time.max()
    )
    logger_data = wl_ts_df.reset_index().rename(
        columns={"loc_id": "unit_hyphen", "corr_end_time": "latest_logger_data"}
    )

    if len(df):
        df2 = df.groupby("dh_no").apply(process_group).reset_index()
    else:
        df2 = pd.DataFrame(
            columns=[
                "dh_no",
                "n_records",
                "latest_obs_date",
                "latest_dtw",
                "latest_swl",
                "latest_rswl",
                "latest_anomalous_ind",
                "latest_comment",
            ]
        )

    df3 = pd.merge(
        wells[["dh_no", "obs_no", "unit_hyphen", "dh_name", "aquifer"]],
        df2,
        on="dh_no",
        how="left",
    )
    df3["n_records"] = df3.apply(
        lambda row: f"<a href='/app/well_combined_water_level?dh_no={row.dh_no}&env={query.env}'>{row.n_records}</a>",
        axis=1,
    )

    df3 = pd.merge(df3, logger_data, on="unit_hyphen", how="left")
    cols = [
        "n_records",
        "latest_obs_date",
        "latest_logger_data",
        "latest_dtw",
        "latest_swl",
        "latest_rswl",
        "latest_anomalous_ind",
        "latest_comment",
    ]

    df_for_table = webapp_utils.prep_table_for_html(df3, cols=cols, query=query)
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in dh_nos]) + ")"
    )

    return templates.TemplateResponse(
        "wells_water_level.html",
        {
            "request": request,
            "env": query.env,
            "redirect_to": "wells_salinity",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_water_level",
            "query": query,
            "wells_title": title,
            "wells_query_params": query_params,
            "result": result,
            "table": table,
            "wells": wells,
            "egis_layer_definition_query": egis_layer_definition_query,
        },
    )


# @router.get("/wells_geojson_summary")
# def wells_map(
#     request: Request,
#     query: Annotated[query_models.Wells, Depends()],
# ):
#     db = connect_to_sageodata(service_name=query.env)
#     wells, name, name_safe, query_params = query.find_wells()
#     dh_nos = wells.dh_no.unique()
#     title = name

#     df = run_wells_query(db, "wells_summary", dh_nos)

#     df = df.sort_values([query.sort])

#     features = []
#     for idx, row in df.iterrows():
#         feature = Feature(geometry=Point(()))

#     return templates.TemplateResponse(
#         "wells_map.html",
#         {
#             "request": request,
#             "query": query,
#             "env": query.env,
#             "redirect_to": "wells_map",
#             "singular_redirect_to": "well_summary",
#             "plural_redirect_to": "wells_map",
#             "title": title,
#             "wells_title": title,
#             "wells_query_params": query_params,
#             "wells": df,
#         },
#     )


@router.get("/wells_drillhole_notes")
def wells_drillhole_notes(
    request: Request,
    query: Annotated[query_models.Wells, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)
    wells, name, name_safe, query_params = query.find_wells()
    dh_nos = wells.dh_no.unique()
    title = name

    result = process_wells_result(db, dh_nos)

    df = run_wells_query(db, "wells_summary", dh_nos)

    df = df.sort_values(
        [query.sort], ascending=True if query.order.startswith("asc") else False
    )

    df2 = db.wells_summary(dh_nos)
    notes = db.drillhole_notes(dh_nos)

    df3 = pd.merge(
        df2,
        notes[
            [
                "dh_no",
                "note_date",
                "note",
                "author",
                "created_by",
                "creation_date",
                "modified_by",
                "modified_date",
            ]
        ],
        on="dh_no",
        how="outer",
    )

    df3 = df3.sort_values(["dh_no", "note_date"], ascending=False)

    def safe_datefmt(v):
        try:
            return v.strftime("%d/%m/%Y")
        except:
            return ""

    df3["note_date"] = df3.note_date.apply(lambda v: f"{safe_datefmt(v)}<wbr>")

    cols = [
        "note_date",
        "note",
        "author",
    ]

    df_for_table = webapp_utils.prep_table_for_html(
        df3, cols=cols, set_index=["note_date", "author"], query=query
    )
    table = webapp_utils.frame_to_html(df_for_table)

    egis_layer_definition_query = (
        "DHNO IN (" + ",".join([str(dh_no) for dh_no in df.dh_no]) + ")"
    )

    return templates.TemplateResponse(
        "wells_drillhole_notes.html",
        {
            "request": request,
            "env": query.env,
            "title": title,
            "query": query,
            "redirect_to": "wells_drillhole_notes",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_drillhole_notes",
            "wells_title": title,
            "wells_query_params": query_params,
            "wells": df,
            "wells_table": table,
            "egis_layer_definition_query": egis_layer_definition_query,
            "result": result,
        },
    )
