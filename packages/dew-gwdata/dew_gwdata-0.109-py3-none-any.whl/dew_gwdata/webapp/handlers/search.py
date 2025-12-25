from pathlib import Path
import urllib.parse
import logging

from fastapi import APIRouter, Request, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sageodata_db import connect as connect_to_sageodata

from dew_gwdata.webapp import utils as webapp_utils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


async def get_body(request: Request):
    return await request.body()


@router.get("/well_find")
def well_find(
    request: Request,
    query: str,
    env: str = "prod",
    unit_no: bool = False,
    obs_no: bool = False,
    dh_no: bool = False,
    singular_search_only: bool = False,
    redirect_to: str = "well_summary",
):
    db = connect_to_sageodata(service_name=env)
    kwargs = {
        k: v
        for k, v in request.query_params.items()
        if not k
        in [
            "query",
            "env",
            "unit_no",
            "obs_no",
            "dh_no",
            "singular_search_only",
            "redirect_to",
        ]
    }
    types = []
    if unit_no:
        types.append("unit_no")
    if obs_no:
        types.append("obs_no")
    if dh_no:
        types.append("dh_no")
    if singular_search_only:
        # Try and search dh_no only if there is no result
        wells = db.find_wells(query, types=[t for t in types if not t == "dh_no"])
        if len(wells) == 0:
            wells = db.find_wells(query, types=types)
        if len(wells) > 0 and len(wells) > 1:
            wells = wells.iloc[:1]
    else:
        wells = db.find_wells(query, types=types)
    if len(wells) == 0:
        raise Exception("No wells found")
    elif len(wells) == 1:
        passthrough_kws = "&".join([f"{k}={v}" for k, v in kwargs.items()])
        if passthrough_kws:
            extra = "&" + passthrough_kws
        else:
            extra = ""
        return RedirectResponse(
            f"/app/{redirect_to}?dh_no={wells.iloc[0].dh_no:.0f}&redirect_to={redirect_to}&env={env}"
            + extra
        )
    else:
        return RedirectResponse(
            f"/app/wells_find?query={query}&unit_no={unit_no}&obs_no={obs_no}&dh_no={dh_no}&redirect_to={redirect_to}&env={env}"
        )


@router.get("/wells_find")
def wells_find(
    request: Request,
    query: str,
    env: str = "prod",
    unit_no: bool = False,
    obs_no: bool = False,
    dh_no: bool = False,
    redirect_to: str = "wells_summary",
):
    db = connect_to_sageodata(service_name=env)
    types = []
    if unit_no:
        types.append("unit_no")
    if obs_no:
        types.append("obs_no")
    if dh_no:
        types.append("dh_no")
    print(f"looking for types: {types}")
    wells = db.find_wells(query, types=types)
    print(f"Found wells: \n{wells}")
    if len(wells) == 0:
        raise Exception("No wells found")
    elif len(wells) == 1:
        if redirect_to == "wells_summary":
            redirect_to = "well_summary"
        return RedirectResponse(
            f"/app/{redirect_to}?dh_no={wells.iloc[0].dh_no:.0f}&env={env}"
        )
    else:
        url_str = webapp_utils.dhnos_to_urlstr(wells.dh_no)
        return RedirectResponse(f"/app/{redirect_to}?url_str={url_str}&env={env}")


@router.post("/wells_find_post")
def wells_find_post(
    request: Request,
    payload_bytes: bytes = Depends(get_body),
    redirect_to: str = "wells_summary",
):
    payload_str = payload_bytes.decode("ascii")
    payload = {}
    for kv in payload_str.split("&"):
        key, value = kv.split("=")
        payload[key] = value
    unit_no = payload.get("unit_no", 0)
    obs_no = payload.get("obs_no", 0)
    dh_no = payload.get("dh_no", 0)
    query = payload.get("query", "")
    env = payload.get("env", "prod")

    db = connect_to_sageodata(service_name=env)
    types = []
    if unit_no:
        types.append("unit_no")
    if obs_no:
        types.append("obs_no")
    if dh_no:
        types.append("dh_no")
    logger.info(f"looking for types: {types} in query = {query[:30]}...{query[-30:]}")
    wells = db.find_wells(urllib.parse.unquote(query), types=types, dh_re_prefix="")
    logger.info(f"Found {len(wells)} wells.")
    if len(wells) == 0:
        raise Exception("No wells found")
    elif len(wells) == 1:
        if redirect_to == "wells_summary":
            redirect_to = "well_summary"
        return RedirectResponse(
            f"/app/{redirect_to}?dh_no={wells.iloc[0].dh_no:.0f}&env={env}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    else:
        url_str = webapp_utils.dhnos_to_urlstr(wells.dh_no)
        logger.info(
            f"{len(wells)} wells identified, redirecting via url_str length {len(url_str)}"
        )
        return RedirectResponse(
            f"/app/wells_summary?url_str={url_str}&env={env}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.get("/wells_search_name")
def wells_search_name(
    request: Request,
    query: str,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    wells = db.drillhole_details_by_name_search(query)
    if len(wells) == 0:
        raise Exception("No wells found")
    elif len(wells) == 1:
        return RedirectResponse(
            f"/app/well_summary?dh_no={wells.iloc[0].dh_no:.0f}&env={env}"
        )
    else:
        url_str = webapp_utils.dhnos_to_urlstr(wells.dh_no)
        return RedirectResponse(f"/app/wells_summary?url_str={url_str}&env={env}")


@router.get("/wells_search_around")
def wells_search_around(
    request: Request,
    query: str,
    env: str = "prod",
    unit_no: bool = False,
    obs_no: bool = False,
    dh_no: bool = False,
    singular_search_only: bool = True,
    distance: float = 1,
    redirect_to: str = "wells_summary",
):
    db = connect_to_sageodata(service_name=env)
    types = []
    if unit_no:
        types.append("unit_no")
    if obs_no:
        types.append("obs_no")
    if dh_no:
        types.append("dh_no")

    query_well = None
    if singular_search_only:
        # Try and search dh_no only if there is no result
        wells = db.find_wells(query, types=[t for t in types if not t == "dh_no"])
        if len(wells) == 0:
            wells = db.find_wells(query, types=types)
        if len(wells) > 0:
            query_well = wells.iloc[0]
    else:
        wells = db.find_wells(query, types=types)
        if len(wells) > 0:
            query_well = wells.iloc[0]

    if query_well is None:
        raise Exception("No well found with query.")

    wells = db.drillhole_within_distance(query_well.dh_no, distance)
    url_str = webapp_utils.dhnos_to_urlstr(wells.dh_no)
    return RedirectResponse(f"/app/{redirect_to}?url_str={url_str}&env={env}")
