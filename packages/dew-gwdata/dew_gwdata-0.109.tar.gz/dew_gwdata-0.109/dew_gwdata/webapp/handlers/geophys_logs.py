from pathlib import Path
from typing import Annotated
import urllib.parse
import logging

import pandas as pd
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sageodata_db import connect as connect_to_sageodata

import dew_gwdata as gd
from dew_gwdata.webapp import utils as webapp_utils
from dew_gwdata.webapp import query_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


@router.get("/geophys_logs_summary")
def geophys_logs_summary(
    request: Request,
    query: Annotated[query_models.GeophysLogJobs, Depends()],
):
    db = connect_to_sageodata(service_name=query.env)
    df, title, query_params = query.find_jobs()

    df = df.sort_values(query.sort, ascending=query.order == "ascending")

    title_series = df.apply(
        lambda well: (
            (
                f'<nobr><a href="/app/well_summary?dh_no={well.dh_no}&env={query.env}">'
                f'{webapp_utils.make_dh_title(well, elements=("unit_no", "obs_no"))}</a></nobr>'
            )
            if not pd.isnull(well.dh_no)
            else ""
        ),
        axis=1,
    )
    df.insert(0, "title", title_series)
    df = df.drop(["well_id", "unit_hyphen", "obs_no"], axis=1)
    df.insert(4, "suburb", gd.locate_wells_in_suburbs(df))

    df["aquifer"] = df.aquifer.fillna("")
    df["aquifer"] = df.apply(
        lambda row: f"<a href='/app/aquifer_unit?aquifer_code={row.aquifer}&env={query.env}'>{row.aquifer}</a>",
        axis=1,
    )

    # http://bunyip:8191/app/well_geophysical_logs?dh_no=25528&env=PROD#68
    # df.loc[~pd.isnull(df.dh_no), "job_no"] = df.apply(
    #     lambda row: f"<a href='/app/well_geophysical_logs?dh_no={row.dh_no}&env={query.env}#{row.job_no}'>{row.job_no}</a>",
    #     axis=1,
    # )
    # df.loc[pd.isnull(df.dh_no), "job_no"] = df.apply(
    df["job_no"] = df.apply(
        lambda row: f"<a href='/app/geophysical_logging_job?job_no={row.job_no}&env={query.env}'>{row.job_no}</a>",
        axis=1,
    )

    valid_dh_nos = [dh_no for dh_no in df.dh_no.dropna().unique()]
    wells_query_params = "url_str=" + webapp_utils.dhnos_to_urlstr(
        [int(dh_no) for dh_no in valid_dh_nos]
    )

    df["dh_no"] = df.dh_no.apply(lambda n: f"{n:.0f}" if not pd.isnull(n) else "")

    df = df.drop(
        [
            "log_hdr_no",
            "log_easting",
            "log_northing",
            "log_zone",
            "log_latitude",
            "log_longitude",
            "unit_long",
            "easting",
            "northing",
            "zone",
            "latitude",
            "longitude",
            "gl_dh_name",
            "project",
        ],
        axis=1,
    )

    table = webapp_utils.frame_to_html(df)

    return templates.TemplateResponse(
        "geophys_logs_summary.html",
        {
            "request": request,
            "env": query.env,
            "title": title,
            "redirect_to": "group_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "query": query,
            "df": df,
            "table": table,
            "valid_dh_nos": valid_dh_nos,
            "wells_query_params": wells_query_params,
        },
    )


@router.get("/geophysical_logging_job")
def geophysical_logging_job(
    request: Request,
    job_no: int,
    env: str = "prod",
) -> str:
    db = connect_to_sageodata(service_name=env)
    logger.debug(f"job_no={job_no}")
    job_nos = [job_no]
    md = db.geophys_log_metadata_by_job_no(job_nos)
    logger.debug(f"length md={len(md)}")
    files = gd.list_geophys_job_files(job_nos=job_nos, add_las_metadata=True)
    logger.debug(f"found n files={len(files)}")

    dh_no = md.dh_no.iloc[0]
    dh_no_link = "Not linked (unidentified or maybe Victorian)"
    if dh_no:
        well = db.drillhole_details([dh_no]).iloc[0]
        well_title = webapp_utils.make_dh_title(well)
        dh_no_link = (
            f"<a href='/app/well_summary?dh_no={dh_no}&env={env}'>{well_title}</a>"
        )

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

    files.loc[files.file_type == "LAS", "log_types"] = files.apply(
        link_log_types, axis=1
    )
    files.loc[files.file_type == "LAS", "mnemonics"] = files.apply(
        link_log_mnemonics, axis=1
    )
    img = '<img src="/static/download.svg" width="14px" height="14px" />'
    if len(files):
        files.loc[files.file_type == "LAS", "csv_download"] = files.apply(
            lambda row: f"<a href='/api/well_geophysical_las_file_data?job_no={row.job_no}&filename={urllib.parse.quote(row.filename)}'>{img}</a>",
            axis=1,
        )
    else:
        files["csv_download"] = ""
    files["filename"] = files.filename.apply(
        lambda filename: f"<a href='/api/well_geophysical_log_file?job_no={job_no}&filename={urllib.parse.quote(filename)}'>{filename}</a>"
    )
    files_cols = [
        "filename",
        "file_type",
        "file_size",
        "csv_download",
        "max_depth_las",
        "log_types",
        "mnemonics",
    ]

    files_table = webapp_utils.frame_to_html(
        gd.cleanup_columns(files[files_cols], drop=["path"], keep_cols=[])
    )
    md_table = webapp_utils.series_to_html(
        md.iloc[0],
        transpose=False,
    )

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
        "gl_permit_no",
        "max_log_depth",
        "comments",
    ]
    md_table = webapp_utils.frame_to_html(gd.cleanup_columns(md, keep_cols=[])[md_cols])

    return templates.TemplateResponse(
        "geophysical_logging_job.html",
        {
            "request": request,
            "env": env,
            "title": f"GL job {job_no}",
            "dh_no_link": dh_no_link,
            "dh_no": dh_no,
            "job_no": job_no,
            # "redirect_to": "well_geophysical_logs",
            # "singular_redirect_to": "well_geophysical_logs",
            # "plural_redirect_to": "wells_summary",
            # "wells_title": "1 well",
            # "wells_query_params": "url_str=" + webapp_utils.dhnos_to_urlstr([dh_no]),
            # "well": well,
            "md": md,
            "files": files,
            "md_table": md_table,
            "files_table": files_table,
        },
    )
