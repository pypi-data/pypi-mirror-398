from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sageodata_db import connect as connect_to_sageodata

import dew_gwdata as gd
from dew_gwdata.webapp import utils as webapp_utils
from dew_gwdata.webapp import query_models


router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


@router.get("/strat_units")
def strat_units(
    request: Request,
    query: Annotated[query_models.StratUnits, Depends()],
):
    strat_unit_nos = query.find_strat_units()
    db = connect_to_sageodata(service_name=query.env)
    details = db.strat_unit_details(strat_unit_nos)
    if len(details) == 1:
        return RedirectResponse(
            f"/app/strat_unit?strat_unit_no={details.strat_unit_no.iloc[0]}&env={query.env}"
        )
    details["map_symbol"] = details.apply(
        lambda row: f"<a href='/app/strat_unit?strat_unit_no={row.strat_unit_no}&env={query.env}'>{row.map_symbol}</a>",
        axis=1,
    )
    details["agso_number"] = details.agso_number.apply(
        lambda n: (
            f"<a href='https://asud.ga.gov.au/search-stratigraphic-units/results/{n}'>{n:.0f}</a>"
            if not pd.isnull(n)
            else ""
        )
    )
    table = webapp_utils.frame_to_html(details)

    return templates.TemplateResponse(
        "strat_units.html",
        {
            "request": request,
            "env": query.env,
            "redirect_to": "strat_units",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "details": details,
            "table": table,
            "map_symbol": query.map_symbol,
            "strat_name": query.strat_name,
        },
    )


@router.get("/aquifer_units")
def aquifer_units(
    request: Request,
    query: Annotated[query_models.AquiferUnits, Depends()],
):
    aquifer_codes = query.find_aquifer_codes()
    db = connect_to_sageodata(service_name=query.env)
    details = db.aquifer_units_details(aquifer_codes)
    details = details.sort_values(["aquifer_code"])
    details["aquifer_code"] = details.apply(
        lambda row: f"<a href='/app/aquifer_unit?aquifer_code={row.aquifer_code}&env={query.env}'>{row.aquifer_code}</a>",
        axis=1,
    )
    details["linked_map_symbol"] = details.apply(
        lambda row: f"<a href='/app/strat_unit?strat_unit_no={row.linked_strat_unit_no}&env={query.env}'>{row.linked_map_symbol}</a>",
        axis=1,
    )
    details["major_map_symbol"] = details.apply(
        lambda row: f"<a href='/app/strat_unit?strat_unit_no={row.major_strat_unit_no}&env={query.env}'>{row.major_map_symbol}</a>",
        axis=1,
    )
    details["linked_strat_agso_number"] = details.linked_strat_agso_number.apply(
        lambda n: (
            f"<a href='https://asud.ga.gov.au/search-stratigraphic-units/results/{n}'>{n:.0f}</a>"
            if not pd.isnull(n)
            else ""
        )
    )
    table = webapp_utils.frame_to_html(details)

    return templates.TemplateResponse(
        "aquifer_units.html",
        {
            "request": request,
            "env": query.env,
            "redirect_to": "aquifer_units",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "details": details,
            "table": table,
            "aquifer_code": query.aquifer_code,
            "aquifer_name": query.aquifer_name,
        },
    )


@router.get("/strat_unit")
def strat_unit(request: Request, strat_unit_no: int, env: str = "PROD"):
    db = connect_to_sageodata(service_name=env)
    details = db.strat_unit_details([strat_unit_no]).iloc[0]
    notes = db.strat_unit_notes([strat_unit_no])
    notes_cols = [
        "note_type",
        "desc_type",
        "note",
        "created_by",
        "creation_date",
        "modified_by",
        "modified_date",
    ]
    notes = notes[notes_cols]
    aq = db.strat_unit_to_aquifer_unit(strat_unit_no)
    aq = aq[["aquifer_code", "hydro_subunit_desc"]]

    lookups, reports_all = gd.generate_aquifer_code_index(
        add_hyperlinks=True, sagd_conn=db
    )
    lookup = lookups[
        (lookups.code == details.map_symbol) & (lookups.code_type == "map_symbol")
    ]
    reports = reports_all[reports_all.filename.isin(lookup.report_filename)]
    reports["filename"] = reports.filename.apply(
        lambda fn: f"<a href='/api/aquifer_database_file?filename={fn}'>{fn}</a>"
    )

    details["agso_number"] = (
        f"<a href='https://asud.ga.gov.au/search-stratigraphic-units/results/{details.agso_number}'>{details.agso_number}</a>"
    )

    aq["aquifer_code"] = aq.aquifer_code.fillna("")
    aq["aquifer_code"] = aq.apply(
        lambda row: f"<a href='/app/aquifer_unit?aquifer_code={row.aquifer_code}&env={env}'>{row.aquifer_code}</a>",
        axis=1,
    )

    details_table = webapp_utils.series_to_html(details, transpose=True)
    notes_table = webapp_utils.frame_to_html(notes)
    aq_table = webapp_utils.frame_to_html(aq)
    reports_table = webapp_utils.frame_to_html(reports)

    return templates.TemplateResponse(
        "strat_unit.html",
        {
            "request": request,
            "env": env,
            "redirect_to": "strat_unit",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "details": details,
            "details_table": details_table,
            "notes_table": notes_table,
            "aq": aq,
            "aq_table": aq_table,
            "map_symbol": details.map_symbol,
            "strat_name": "%",
            "reports_table": reports_table,
        },
    )


@router.get("/aquifer_unit")
def aquifer_unit(request: Request, aquifer_code: str, env: str = "PROD"):
    db = connect_to_sageodata(service_name=env)
    details = db.aquifer_units_details([aquifer_code])
    details["linked_map_symbol"] = details.apply(
        lambda row: f"<a href='/app/strat_unit?strat_unit_no={row.linked_strat_unit_no}&env={env}'>{row.linked_map_symbol}</a>",
        axis=1,
    )
    details["major_map_symbol"] = details.apply(
        lambda row: f"<a href='/app/strat_unit?strat_unit_no={row.major_strat_unit_no}&env={env}'>{row.major_map_symbol}</a>",
        axis=1,
    )
    details["linked_strat_agso_number"] = details.linked_strat_agso_number.apply(
        lambda n: (
            f"<a href='https://asud.ga.gov.au/search-stratigraphic-units/results/{n}'>{n}</a>"
            if not n is None
            else ""
        )
    )
    details_series = details.iloc[0]

    lookups, reports_all = gd.generate_aquifer_code_index(
        add_hyperlinks=True, sagd_conn=db
    )
    lookup = lookups[
        (lookups.code == details_series.aquifer_code)
        & (lookups.code_type == "aquifer_code")
    ]
    reports = reports_all[reports_all.filename.isin(lookup.report_filename)]
    reports["filename"] = reports.filename.apply(
        lambda fn: f"<a href='/api/aquifer_database_file?filename={fn}'>{fn}</a>"
    )

    other_aq = db.strat_unit_to_aquifer_unit(int(details_series.linked_strat_unit_no))
    other_aq = other_aq[["aquifer_code", "hydro_subunit_desc"]]
    other_aq["aquifer_code"] = other_aq.aquifer_code.fillna("")
    other_aq["aquifer_code"] = other_aq.apply(
        lambda row: f"<a href='/app/aquifer_unit?aquifer_code={row.aquifer_code}&env={env}'>{row.aquifer_code}</a>",
        axis=1,
    )

    details_table = webapp_utils.series_to_html(details_series, transpose=True)
    other_aq_table = webapp_utils.frame_to_html(other_aq)
    reports_table = webapp_utils.frame_to_html(reports)

    return templates.TemplateResponse(
        "aquifer_unit.html",
        {
            "request": request,
            "env": env,
            "redirect_to": "strat_unit",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "details": details_series,
            "details_table": details_table,
            "strat_name": "%",
            "aquifer_code_encoded": details_series.aquifer_code,
            "aquifer_code": aquifer_code,
            "aquifer_name": "%",
            "other_aq": other_aq,
            "other_aq_table": other_aq_table,
            "reports_table": reports_table,
        },
    )
