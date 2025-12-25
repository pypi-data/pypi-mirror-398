import datetime
from pathlib import Path
import logging

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sageodata_db import connect as connect_to_sageodata

from dew_gwdata.webapp import utils as webapp_utils


router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)

logger = logging.getLogger(__name__)


@router.get("/data_entry_and_edits")
def data_entry_and_edits(request: Request, env: str = "prod"):
    return templates.TemplateResponse(
        "data_entry_and_edits.html",
        {
            "request": request,
            "title": "Data entry and edit tracking",
            "env": env,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
        },
    )


@router.get("/salinity_data_entry_by_day")
def salinity_data_entry_by_day(
    request: Request,
    start_timestamp: str = "2023-01-01",
    end_timestamp: str = "today",
    env: str = "PROD",
):
    if start_timestamp == "":
        start_timestamp = "1997-01-01"
    if end_timestamp == "today" or end_timestamp == "":
        end_timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    db = connect_to_sageodata(service_name=env)
    query_end_ts = (pd.Timestamp(end_timestamp) + pd.Timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    df = db.salinity_data_entry_from_year(start_timestamp, query_end_ts)
    if len(df):
        df["count_unique_wells"] = df.apply(
            lambda row: f"<a href='/app/wells_salinity?salinity_creation_date={row.creation_date.strftime('%Y-%m-%d')}&salinity_created_by={row.created_by}&env={env}'>{row.count_unique_wells}</a>",
            axis=1,
        )

    table = webapp_utils.frame_to_html(df)

    return templates.TemplateResponse(
        "salinity_data_entry_by_day.html",
        {
            "request": request,
            "title": "Recent salinity data entry into SA Geodata",
            "env": env,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "table": table,
        },
    )


@router.get("/water_level_data_entry_by_day")
def water_level_data_entry_by_day(
    request: Request,
    start_timestamp: str = "2023-01-01",
    end_timestamp: str = "today",
    env: str = "PROD",
):
    if start_timestamp == "":
        start_timestamp = "1997-01-01"
    if end_timestamp == "today" or end_timestamp == "":
        end_timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    db = connect_to_sageodata(service_name=env)
    query_end_ts = (pd.Timestamp(end_timestamp) + pd.Timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    df = db.water_level_data_entry_from_year(start_timestamp, query_end_ts)
    if len(df):
        df["count_unique_wells"] = df.apply(
            lambda row: f"<a href='/app/wells_water_level?wl_creation_date={row.creation_date.strftime('%Y-%m-%d')}&wl_created_by={row.created_by}&wl_measured_during={row.measured_during}&env={env}'>{row.count_unique_wells}</a>",
            axis=1,
        )

    table = webapp_utils.frame_to_html(df)

    return templates.TemplateResponse(
        "water_level_data_entry_by_day.html",
        {
            "request": request,
            "title": "Recent water level data entry into SA Geodata",
            "env": env,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "table": table,
        },
    )


@router.get("/aquifer_mon_edits")
def aquifer_mon_edits(
    request: Request,
    start_timestamp: str = "2024-04-01",
    end_timestamp: str = "today",
    env: str = "PROD",
):
    if start_timestamp == "":
        start_timestamp = "1997-01-01"
    if end_timestamp == "today" or end_timestamp == "":
        end_timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    db = connect_to_sageodata(service_name=env)
    logger.debug(f"start_timestamp = {start_timestamp}")
    query_end_ts = (pd.Timestamp(end_timestamp) + pd.Timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )

    def construct_hyperlink(row):
        query_params = [
            "edit_timestamp=" + row.latest_edited_date.strftime("%Y-%m-%d"),
            "edit_by=" + row.latest_edited_by,
            "edit_type=aquifer_mon",
        ]
        url = f"/app/wells_aquifer_mon?" + "&".join(query_params)
        return f"<a href='{url}'>{row.count_wells}"

    df = db.data_edits_aquifer_mon(start_timestamp, query_end_ts)
    if len(df):
        df["count_wells"] = df.apply(construct_hyperlink, axis=1)

    table = webapp_utils.frame_to_html(df)

    return templates.TemplateResponse(
        "aquifer_mon_edits.html",
        {
            "request": request,
            "env": env,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "title": "Recent aquifer code edits in SA Geodata",
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "table": table,
        },
    )


@router.get("/erroneous_aquifer_units")
def erroneous_aquifer_units(
    request: Request,
    env: str = "PROD",
):
    db = connect_to_sageodata(service_name=env)
    df = db.erroneous_aquifer_units()
    df["major_unit"] = df.apply(lambda row: f"<a href=/app/well_summary?")
    df_for_table = webapp_utils.prep_table_for_html(df, env=env)
    df_for_table = df_for_table.drop(["aquifer"], axis=1)
    table = webapp_utils.frame_to_html(df_for_table)

    return templates.TemplateResponse(
        "erroneous_aquifer_units.html",
        {
            "request": request,
            "title": "Erroneously entered aquifer monitored designations in SA Geodata",
            "env": env,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_aquifer_mon",
            "table": table,
        },
    )
