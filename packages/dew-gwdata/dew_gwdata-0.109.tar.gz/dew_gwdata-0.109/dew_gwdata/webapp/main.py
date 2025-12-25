import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dew_gwdata.webapp.handlers import (
    api,
    home,
    geophys_logs,
    schema,
    search,
    permit,
    well,
    wells,
    groups,
    data_entry,
    strat,
    rainfall,
)

logger = logging.getLogger(__name__)


app = FastAPI(debug=True)

static_path = Path(__file__).parent / "static"
pydocs_path = (
    Path(r"r:\dfw_cbd")
    / "projects"
    / "projects_gw"
    / "state"
    / "groundwater_toolbox"
    / "python"
    / "wheels"
    / "docs"
)

app.mount("/python-docs", StaticFiles(directory=pydocs_path), name="pydocs_path")
app.mount("/static", StaticFiles(directory=static_path), name="static")
app.mount(
    "/nap-preliminary-transfer-assessment-fy2425-qa",
    StaticFiles(
        directory=r"r:\dfw_cbd\projects\Projects_GW\Regional\St_Vincent_Basin\NAP_PWA\WAP_NAP_transfers\FY24-25_Prelim_Tool\QA"
    ),
    name="nap_tool_fy2425_qa",
)

app.include_router(api.router)
app.include_router(data_entry.router)
app.include_router(home.router)
app.include_router(geophys_logs.router)
app.include_router(groups.router)
app.include_router(schema.router)
app.include_router(search.router)
app.include_router(strat.router)
app.include_router(well.router)
app.include_router(wells.router)
app.include_router(permit.router)
app.include_router(rainfall.router)
