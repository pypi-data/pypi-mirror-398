from pathlib import Path
from typing import Annotated
import re
import logging

import numpy as np
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


@router.get("/permits")
def permits(
    request: Request,
    query: Annotated[query_models.Permits, Depends()],
):
    permits, title, query_params = query.find_permits()
    db = connect_to_sageodata(service_name=query.env)
    permits["permit_no"] = permits.permit_no.apply(
        lambda p: f"<a href='/app/permit?permit_no={p}&env={query.env}'>{p}</a>"
    )
    permits.loc[permits.existing_unit_hyphen == "-", "existing_unit_hyphen"] = ""

    unit_nos = " ".join(permits.existing_unit_hyphen.unique())
    wells = db.find_wells(unit_nos).set_index("unit_hyphen").dh_no.to_dict()

    permits["existing_unit_hyphen"] = permits.existing_unit_hyphen.apply(
        lambda unit_hyphen: (
            f"<a href='/app/well_summary?dh_no={wells[unit_hyphen]}&env={query.env}'>{unit_hyphen}</a>"
            if unit_hyphen in wells
            else unit_hyphen
        )
    )
    permits["permit_holder_address"] = permits.permit_holder_address.apply(
        lambda x: str(x).replace(r"\n", " ")
    )
    permits_table = webapp_utils.frame_to_html(permits)

    return templates.TemplateResponse(
        "permits.html",
        {
            "request": request,
            "env": query.env,
            "query": query,
            "title": title,
            # "redirect_to": "strat_units",
            # "singular_redirect_to": "well_summary",
            # "plural_redirect_to": "wells_summary",
            "permits": permits,
            "permits_table": permits_table,
        },
    )


@router.get("/permit")
def permit(request: Request, permit_no: str, env: str = "PROD"):
    permit_no = int(re.match(r"\d*", permit_no).group())
    db = connect_to_sageodata(service_name=env)
    details = db.permit_details([permit_no]).iloc[0]
    notes = db.permit_conditions_and_notes([permit_no])

    dhs_cols = [
        "site_extension",
        "completion_date",
        "activity",
        "dh_no",
        "unit_hyphen",
        "obs_no",
        "dh_name",
        "total_depth",
        "final_depth",
        "driller_name",
        "plant_operator",
        "comments",
    ]
    other_cols = [
        "permit_no_only",
        "site_extension",
        "completion_date",
        "activity",
        "dh_no",
        "unit_hyphen",
        "obs_no",
        "dh_name",
        "total_depth",
        "final_depth",
        "driller_name",
        "plant_operator",
        "comments",
    ]

    dhs = db.drillhole_construction_by_permit_nos([permit_no])
    dhs = gd.add_construction_activity_column(dhs)
    if len(dhs):
        other = db.construction_events(dhs.dh_no)
        other = other[other.event_type == "C"]
        other = other[other.permit_no_only != permit_no]
        other = gd.add_construction_activity_column(other)
    else:
        other = pd.DataFrame(columns=other_cols)

    wells = db.find_wells(details.existing_unit_hyphen)
    if len(wells):
        details["existing_unit_hyphen"] = (
            f"<a href='/app/well_summary?dh_no={wells.iloc[0].dh_no}&env={env}'>{details.existing_unit_hyphen}</a>"
        )

    dhs["unit_hyphen"] = dhs.apply(
        lambda row: f"<a href='/app/well_summary?dh_no={row.dh_no}&env={env}'>{row.unit_hyphen}</a>",
        axis=1,
    )
    other["unit_hyphen"] = other.apply(
        lambda row: f"<a href='/app/well_summary?dh_no={row.dh_no}&env={env}'>{row.unit_hyphen}</a>",
        axis=1,
    )
    other["permit_no_only"] = other.permit_no_only.apply(
        lambda pn: (
            f"<a href='/app/permit?permit_no={pn}&env={env}'>{int(pn)}</a>"
            if not np.isnan(pn)
            else ""
        )
    )

    details_table = webapp_utils.series_to_html(details)
    notes_table = webapp_utils.frame_to_html(notes)
    dhs_table = webapp_utils.frame_to_html(dhs[dhs_cols])
    other_table = webapp_utils.frame_to_html(other[other_cols])

    title = f"PN {permit_no}"

    return templates.TemplateResponse(
        "permit.html",
        {
            "request": request,
            "env": env,
            "title": title,
            "permit_no": permit_no,
            "details": details,
            "details_table": details_table,
            "notes_table": notes_table,
            "dhs_table": dhs_table,
            "other_table": other_table,
        },
    )
