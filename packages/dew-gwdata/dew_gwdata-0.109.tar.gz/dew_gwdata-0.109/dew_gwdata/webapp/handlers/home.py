from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from dew_gwdata import __version__

router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


@router.get("/")
def home_handler(request: Request) -> str:
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": f'dew_gwdata.webapp {__version__} ("Waterkennect") home page',
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "env": "prod",
        },
    )
