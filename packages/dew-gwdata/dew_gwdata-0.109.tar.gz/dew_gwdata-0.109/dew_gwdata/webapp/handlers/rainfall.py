from datetime import datetime
from pathlib import Path
from typing import Annotated
import logging

import pandas as pd
import geopandas as gpd
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import ausweather

import dew_gwdata as gd
from dew_gwdata.webapp import utils as webapp_utils
from dew_gwdata.webapp import query_models


router = APIRouter(prefix="/app", include_in_schema=False)

templates_path = Path(__file__).parent.parent / "templates"

templates = Jinja2Templates(directory=templates_path)


logger = logging.getLogger(__name__)


@router.get("/rainfall_stations")
def rainfall_stations(
    request: Request,
    query: Annotated[query_models.RainfallStations, Depends()],
):
    df, title, query_params = query.find_stations()

    if len(df) == 1:
        return RedirectResponse(f"/app/rainfall_station?{query_params}")

    title_series = df.apply(
        lambda row: (
            f'<nobr><a href="/app/rainfall_station?station_id={row.station_id}">'
            f"{row.station_id}</a></nobr>"
        ),
        axis=1,
    )
    df.insert(0, "title", title_series)

    gdf = gpd.GeoDataFrame(
        df[["station_id"]],
        geometry=gpd.points_from_xy(df["lon"], df["lat"], crs="epsg:7844"),
    )
    gdf["suburb"] = gd.locate_points_in_suburbs(gdf)
    df2 = pd.merge(df, gdf, on="station_id", how="left")

    cols = [
        "title",
        "station_id",
        "suburb",
        "station_name",
        "distance_km",
        "start",
        "end",
        "current",
        "total_span_yrs",
        "aws",
        "state",
    ]
    if not "distance_km" in df2:
        cols = [c for c in cols if not c == "distance_km"]
    else:
        df2["distance_km"] = df2.distance_km.round(1)
    df2 = df2[cols]
    df2["total_span_yrs"] = df2.total_span_yrs.round(0).astype(int)
    df2.loc[df2.current == False, "current"] = ""
    df2.loc[df2.aws == False, "aws"] = ""

    table = webapp_utils.frame_to_html(df2)

    return templates.TemplateResponse(
        "rainfall_stations.html",
        {
            "request": request,
            # "redirect_to": "group_summary",
            # "singular_redirect_to": "well_summary",
            # "plural_redirect_to": "wells_summary",
            "query": query,
            "df": df2,
            "table": table,
        },
    )


@router.get("/rainfall_station")
def rainfall_station(
    request: Request,
    query: Annotated[query_models.RainfallStations, Depends()],
    avg_pd_start: str = "",
    avg_pd_end: str = "",
    fetch_from_silo: bool = False,
    chart_length_months: int = 0,
):
    df, title, query_params = query.find_stations()
    now = datetime.now()

    try:
        avg_pd_start = int(avg_pd_start)
    except:
        avg_pd_start = None
    try:
        avg_pd_end = int(avg_pd_end)
    except:
        avg_pd_end = now.year

    if len(df) != 1:
        return RedirectResponse(f"/app/rainfall_stations?{query_params}")

    site = df.iloc[0]

    app_db = gd.connect_to_package_database()
    rf0 = webapp_utils.load_rainfall_from_db(site.station_id, app_db)
    currency = datetime.now() - rf0.daily.date_added.max()

    if len(rf0.daily) == 0:
        fetch_from_silo = True
    elif pd.isnull(rf0.daily.date.max()):
        fetch_from_silo = True
    elif currency > pd.Timedelta(days=30):
        fetch_from_silo = True
    else:
        fetch_from_silo = fetch_from_silo
    if fetch_from_silo:
        rf1 = ausweather.RainfallStationData.from_bom_via_silo(
            site.station_id,
            "groundwater@sa.gov.au",
            clip_ends=False,
            data_end=pd.Timestamp(datetime.now()),
        )
        webapp_utils.write_daily_rainfall_to_db(site.station_id, rf1.daily, app_db)
        rf = webapp_utils.load_rainfall_from_db(site.station_id, app_db)
        message = "Data fetched live from SILO Patched Point Data website."
    else:
        rf = webapp_utils.load_rainfall_from_db(site.station_id, app_db)
        message = f"Data fetched from local database cache as it has been updated in the last 30 days (last data point is {currency} ago)"

    app_db.close()

    # Compile annual data and chart
    if avg_pd_start is None:
        avg_pd_start = rf.calendar.year.min()

    annual_st = ausweather.annual_stats(
        rf.calendar, avg_pd_start=avg_pd_start, avg_pd_end=avg_pd_end
    )
    annual_st = {
        k: v
        for k, v in annual_st.items()
        if k in ["min", "pct5", "pct25", "mean", "median", "pct75", "pct95", "max"]
    }
    annual_st = pd.Series(annual_st)[
        ["min", "pct5", "pct25", "mean", "median", "pct75", "pct95", "max"]
    ].round(decimals=1)

    annual = (
        rf.daily.groupby(["year", "interpolated_desc"])
        .rainfall.sum()
        .unstack(level=1)
        .fillna(0)
        .reset_index()
    )

    cols_for_annual_record = [
        "year",
        "total",
        "observed",
        "deaccumulated",
        "interpolated",
        "mean",
        "pct5",
        "pct95",
    ]
    annual["mean"] = annual_st["mean"]
    annual["pct5"] = annual_st["pct5"]
    annual["pct95"] = annual_st["pct95"]
    for col in cols_for_annual_record:
        if not col in annual:
            annual[col] = 0
    annual["total"] = annual.observed + annual.deaccumulated + annual.interpolated

    annual_chart_rows = []
    for idx, record in annual.iterrows():
        record = record.to_dict()
        row_values = [
            webapp_utils.fmt_for_js(record[col]) for col in cols_for_annual_record
        ]
        row = "[" + ", ".join(row_values) + "]"
        annual_chart_rows.append(row)
    calendar_js_dataset = ",\n ".join(annual_chart_rows)

    # Compile monthly data and chart

    monthly = pd.DataFrame(rf.month)
    logger.debug(
        f"before monthly validation. avg_pd_start={avg_pd_start} avg_pd_end={avg_pd_end}"
    )

    if not avg_pd_start:
        monthly_avg_pd_start = (avg_pd_start, 1)
    else:
        monthly_avg_pd_start = None

    if not avg_pd_end:
        monthly_avg_pd_end = (avg_pd_end, 12)
    else:
        monthly_avg_pd_end = None

    logger.debug(
        f"after validation. monthly_avg_pd_start={monthly_avg_pd_start} monthly_avg_pd_end={monthly_avg_pd_end}"
    )

    monthly_st = ausweather.monthly_stats(
        rf.month, avg_pd_start=monthly_avg_pd_start, avg_pd_end=monthly_avg_pd_end
    )
    monthly_st_values = monthly_st[
        ["min", "pct5", "pct25", "mean", "median", "pct75", "pct95", "max"]
    ].round(1)

    chart_end_index = rf.month.loc[
        (rf.month.year == now.year) & (rf.month.month == now.month)
    ].index[0]
    monthly = rf.month.iloc[0:chart_end_index]
    year_span = monthly.year.max() - monthly.year.min()
    pct_2_years = 2 / year_span * 100

    for st_col in ["pct5", "pct25", "mean", "pct75", "pct95"]:
        monthly[st_col] = monthly.month.map(monthly_st[st_col])

    monthly["total"] = monthly["rainfall"]

    cols_for_monthly_record = [
        "year",
        "month",
        "year_month",
        "total",
        "mean",
        "pct5",
        "pct25",
        "pct75",
        "pct95",
    ]
    monthly_chart_rows = []
    for idx, record in monthly.iterrows():
        record = record.to_dict()
        row_values = [
            webapp_utils.fmt_for_js(record[col]) for col in cols_for_monthly_record
        ]
        row = "[" + ", ".join(row_values) + "]"
        monthly_chart_rows.append(row)
    monthly_js_dataset = ",\n ".join(monthly_chart_rows)

    site_bom_url = f"http://www.bom.gov.au/jsp/ncc/cdio/weatherData/av?p_nccObsCode=136&p_display_type=dailyDataFile&p_startYear=&p_c=&p_stn_num={site.station_id}"
    site["station_id"] = f"<a href='{site_bom_url}'>BoM {site.station_id}</a>"

    site_table = webapp_utils.series_to_html(site, transpose=False)
    annual_st_table = webapp_utils.series_to_html(annual_st, transpose=False)
    monthly_st_table = webapp_utils.frame_to_html(monthly_st_values)

    return templates.TemplateResponse(
        "rainfall_station.html",
        {
            "request": request,
            "title": f"{site.station_id}: {site.station_name}",
            "message": message,
            "query": query,
            "site": site,
            "site_table": site_table,
            "annual_stats": annual_st,
            "annual_stats_table": annual_st_table,
            "monthly_stats": monthly_st,
            "monthly_stats_table": monthly_st_table,
            "calendar_js_dataset": calendar_js_dataset,
            "monthly_js_dataset": monthly_js_dataset,
            "avg_pd_start": avg_pd_start,
            "avg_pd_end": avg_pd_end,
            "avg_pd_start_label": (
                avg_pd_start if avg_pd_start else rf.calendar.year.min()
            ),
            "avg_pd_end_label": avg_pd_end if avg_pd_end else rf.calendar.year.max(),
            "pct_2_years": pct_2_years,
        },
    )
