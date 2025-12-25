from pathlib import Path
import fnmatch

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sageodata_db import connect as connect_to_sageodata

import dew_gwdata as gd
from dew_gwdata.webapp import utils as webapp_utils


router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


@router.get("/groups_summary")
def groups_summary(
    request: Request,
    group_type: str = "",
    filter_group_code: str = "*",
    env: str = "PROD",
):
    db = connect_to_sageodata(service_name=env)
    groups = db.group_details()
    types = db.group_types()

    if group_type:
        groups = groups[groups.group_type == group_type]
    groups = groups[
        groups.apply(
            lambda row: fnmatch.fnmatch(row.group_code, filter_group_code), axis=1
        )
    ]

    df = groups.copy()
    df["sort_index"] = 0
    for i, x in enumerate(
        ["OMN", "PR", "MIN", "ARC", "OMH", "GDC", "GDU", "MDC", "MDU"]
    ):
        df.loc[df.group_type == x, "sort_index"] = i
    df = df.sort_values(["sort_index", "group_code"])
    df = df.drop(["sort_index"], axis=1)

    df["group_code"] = df.group_code.apply(
        lambda code: f'<a href="/app/group_summary?group_code={code}&env={env}">{code}</a>'
    )
    table = webapp_utils.frame_to_html(df)

    return templates.TemplateResponse(
        "groups_summary.html",
        {
            "request": request,
            "env": env,
            "redirect_to": "group_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "group_type": group_type,
            "filter_group_code": filter_group_code,
            # "data": data,
            "df": df,
            "table": table,
        },
    )


@router.get("/group_summary")
def group_summary(
    request: Request,
    group_code: str,
    swl_status: str = "C,H,N",
    tds_status: str = "C,H,N",
    swl_freq: str = "1,2,3,4,6,12,24,R,S,blank",
    tds_freq: str = "1,2,3,4,6,12,24,R,S,blank",
    swl_tds_combine: str = "AND",
    filter_comment: str = "*",
    env: str = "PROD",
):
    group_code = group_code.upper()
    db = connect_to_sageodata(service_name=env)
    groups = db.group_details()
    group = groups[groups.group_code == group_code].iloc[0]
    dhs = db.wells_in_groups([group_code])

    dhs["dh_comments"] = dhs.dh_comments.fillna("")

    swl_freqs = [f.strip() for f in swl_freq.split(",")]
    tds_freqs = [f.strip() for f in tds_freq.split(",")]
    swl_statuses = [s.strip() for s in swl_status.split(",")]
    tds_statuses = [s.strip() for s in tds_status.split(",")]
    if "blank" in swl_freqs:
        swl_freqs.append(None)
    if "blank" in tds_freqs:
        tds_freqs.append(None)

    swl_dhs = dhs[
        dhs.swl_status.isin(swl_statuses) & dhs.swl_freq.isin(swl_freqs)
    ].dh_no
    tds_dhs = dhs[
        dhs.tds_status.isin(tds_statuses) & dhs.tds_freq.isin(tds_freqs)
    ].dh_no
    if swl_tds_combine.lower() == "and":
        dhs = dhs[dhs.dh_no.isin(swl_dhs) & dhs.dh_no.isin(tds_dhs)]
        print(f"reduced to {len(dhs)} because swl_tds_combine == and")
    elif swl_tds_combine.lower() == "or":
        dhs = dhs[dhs.dh_no.isin(swl_dhs) | dhs.dh_no.isin(tds_dhs)]
        print(f"reduced to {len(dhs)} because swl_tds_combine == and")
    dhs = dhs[
        dhs.apply(lambda row: fnmatch.fnmatch(row.dh_comments, filter_comment), axis=1)
    ]

    cols = [
        "title",
        "dh_no",
        "dh_name",
        "aquifer",
        "suburb",
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

    title_series = dhs.apply(
        lambda well: (
            f'<nobr><a href="/app/well_summary?dh_no={well.dh_no}&env={env}">'
            f'{webapp_utils.make_dh_title(well, elements=("unit_no", "obs_no"))}</a></nobr>'
        ),
        axis=1,
    )
    dhs.insert(0, "title", title_series)
    dhs = dhs.drop(["well_id", "unit_hyphen", "obs_no"], axis=1)
    dhs.insert(4, "suburb", gd.locate_wells_in_suburbs(dhs))
    dhs_table = webapp_utils.frame_to_html(dhs[cols])

    return templates.TemplateResponse(
        "group_summary.html",
        {
            "request": request,
            "env": env,
            "redirect_to": "group_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "group": group,
            "dhs": dhs,
            "dhs_table": dhs_table,
            "group_code": group_code,
            "swl_status": swl_status,
            "tds_status": tds_status,
            "swl_freq": swl_freq,
            "tds_freq": tds_freq,
            "filter_comment": filter_comment,
            "swl_tds_combine": swl_tds_combine,
        },
    )
