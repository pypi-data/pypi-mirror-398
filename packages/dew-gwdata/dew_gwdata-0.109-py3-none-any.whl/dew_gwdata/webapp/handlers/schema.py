from pathlib import Path
import urllib.parse

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sageodata_db import connect as connect_to_sageodata

from dew_gwdata.webapp import utils as webapp_utils


router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


@router.get("/schema")
def schema(
    request: Request,
    env: str = "prod",
    filter_by: str = "",
) -> str:
    if "test" in env.lower() or "qa" in env.lower():
        user = "dhdb"
        password = "android22"
    else:
        user = "gwquery"
        password = "gwquery"

    filter_by = filter_by.upper()

    db = connect_to_sageodata(service_name=env, user=user, password=password)

    tables_where = ""
    views_where = ""
    if filter_by:
        tables_where = f"and regexp_like(table_name, '{filter_by}')"
        views_where = f"and regexp_like(view_name, '{filter_by}')"

    tables = db.query(
        f"select owner, table_name from all_tables "
        f"where owner in ('DHDB', 'DHDBVIEW') and not table_name like '%$%' {tables_where} order by table_name"
    )
    views = db.query(
        f"select owner, view_name, text_length as view_definition_length "
        f"from all_views where owner in ('DHDB', 'DHDBVIEW') and not view_name like '%$%' {views_where} order by view_name"
    )

    title = "Tables and views"
    if filter_by:
        title += f" containing '{filter_by}'"

    tables["table_name"] = tables.apply(
        lambda r: f'<a href="/app/schema_data?owner={r.owner}&table_name={r.table_name}&env={env}">{r.table_name}</a>',
        axis=1,
    )
    views["view_definition_length"] = views.apply(
        lambda r: f'<a href="/app/schema_view?owner={r.owner}&view_name={r.view_name}&env={env}">{r.view_definition_length}</a>',
        axis=1,
    )
    views["view_name"] = views.apply(
        lambda r: f'<a href="/app/schema_data?owner={r.owner}&table_name={r.view_name}&env={env}">{r.view_name}</a>',
        axis=1,
    )

    tables_html = webapp_utils.frame_to_html(tables)
    views_html = webapp_utils.frame_to_html(views)

    return templates.TemplateResponse(
        "app_schema.html",
        {
            "request": request,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "env": env,
            "title": title,
            "filter_by": filter_by,
            "tables_html": tables_html,
            "views_html": views_html,
        },
    )


@router.get("/schema_columns")
def schema_columns(
    request: Request,
    env: str = "prod",
    filter_by: str = "",
) -> str:
    if "test" in env.lower() or "qa" in env.lower():
        user = "dhdb"
        password = "android22"
    else:
        user = "gwquery"
        password = "gwquery"

    filter_by = filter_by.upper()

    db = connect_to_sageodata(service_name=env, user=user, password=password)

    cols_where = ""
    if filter_by:
        cols_where = f"and regexp_like(column_name, '{filter_by}')"

    query = (
        f"select owner, table_name, column_name, data_type "
        f"from all_tab_columns where owner in ('DHDB', 'DHDBVIEW') {cols_where}"
    )

    print(f"Query = {query}")

    cols = db.query(query)

    title = "Columns"
    if filter_by:
        title += f" containing '{filter_by}'"

    cols["table_name"] = cols.apply(
        lambda r: f'<a href="/app/schema_data?owner={r.owner}&table_name={r.table_name}&env={env}">{r.table_name}</a>',
        axis=1,
    )

    cols_html = webapp_utils.frame_to_html(cols)

    return templates.TemplateResponse(
        "app_schema_columns.html",
        {
            "request": request,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "env": env,
            "title": title,
            "filter_by": filter_by,
            "cols_html": cols_html,
        },
    )


@router.get("/schema_data")
def schema_data(
    request: Request,
    owner: str,
    table_name: str,
    limit: int = 200,
    transpose: bool = False,
    suffix: str = "",
    env: str = "prod",
    select: str = "*",
    where: str = "",
    order_by: str = "",
) -> str:
    if "test" in env.lower() or "qa" in env.lower():
        user = "dhdb"
        password = "android22"
    else:
        user = "gwquery"
        password = "gwquery"

    db = connect_to_sageodata(service_name=env, user=user, password=password)

    if where:
        where_use = " and " + where
    else:
        where_use = ""

    if order_by:
        order_by_use = " order by " + order_by
    else:
        order_by_use = ""

    if limit != -1:
        final_sql = (
            f"SELECT {select} from (select * from {owner}.{table_name} {suffix}) where rownum <= {limit} "
            + where_use
            + order_by_use
        )
    else:
        if where.strip():
            where_use = "where " + where
        else:
            where_use = ""
        final_sql = f"SELECT {select} from {owner}.{table_name} {suffix} {where_use} {order_by_use}"

    data = db.query(final_sql)

    for col in [
        c
        for c in data.columns
        if c.upper().endswith("_CONTENTS") or c.upper() in ("IMAGE", "IMAGE_CONVERTED")
    ]:
        data[col] = "🗎"

    view = db.query(
        f"select * from all_views where owner = '{owner}' and view_name = '{table_name}'"
    )

    if len(view):
        is_view = True
    else:
        is_view = False

    title = f"{owner}.{table_name}"

    if transpose:
        transpose_last = True
        remove_col_underscores = False
    else:
        transpose_last = False
        remove_col_underscores = True

    data_html = webapp_utils.frame_to_html(
        data,
        transpose_last=transpose_last,
        remove_col_underscores=remove_col_underscores,
    )

    return templates.TemplateResponse(
        "app_schema_data.html",
        {
            "request": request,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "env": env,
            "title": title,
            "owner": owner,
            "table_name": table_name,
            "limit": limit,
            "data_html": data_html,
            "transpose": transpose,
            "is_view": is_view,
            "select": select,
            "where": where,
            "order_by": order_by,
            "final_sql": final_sql,
            "final_sql_encoded": urllib.parse.quote(final_sql.replace("SELECT ", "")),
        },
    )


@router.get("/schema_view")
def schema_view(
    request: Request,
    owner: str,
    view_name: str,
    env: str = "prod",
) -> str:
    if "test" in env.lower() or "qa" in env.lower():
        user = "dhdb"
        password = "android22"
    else:
        user = "gwquery"
        password = "gwquery"

    db = connect_to_sageodata(service_name=env, user=user, password=password)

    data = db.query(
        f"select text from all_views where owner = '{owner}' and view_name = '{view_name}'"
    ).iloc[0]

    title = f"{owner}.{view_name}"

    return templates.TemplateResponse(
        "app_schema_view.html",
        {
            "request": request,
            "redirect_to": "well_summary",
            "singular_redirect_to": "well_summary",
            "plural_redirect_to": "wells_summary",
            "env": env,
            "title": title,
            "owner": owner,
            "view_name": view_name,
            "text": data.text,
        },
    )
