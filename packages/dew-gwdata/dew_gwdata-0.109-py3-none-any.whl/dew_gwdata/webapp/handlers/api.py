import base64
import datetime
import io
import os
from pathlib import Path
from typing import Annotated

import numpy as np
import pandas as pd
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import StreamingResponse, Response
from PIL import Image
import lasio

import dew_gwdata as gd
from dew_gwdata.sageodata_database import connect as connect_to_sageodata
from dew_gwdata.webapp import utils as webapp_utils
from dew_gwdata.webapp import query_models


router = APIRouter(prefix="/api")


def apply_format(data, format="json", response_name="export"):
    data = data.fillna("")
    if format == "json":
        if isinstance(data, pd.Series):
            return data.to_dict()
        if isinstance(data, pd.DataFrame):
            return data.to_dict(orient="records")
    elif format == "csv":
        stream = io.StringIO()
        if isinstance(data, pd.Series):
            data.to_frame().to_csv(stream)
        if isinstance(data, pd.DataFrame):
            data.to_csv(stream)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = (
        f"attachment; filename={response_name}.csv"
    )
    return response


@router.get("/utils_find_wells", tags=["utils"])
def find_wells(
    request: Request,
    query: str,
    env: str = "PROD",
    unit_no: bool = False,
    obs_no: bool = False,
    dh_no: bool = False,
    singular_search_only: bool = False,
):
    db = connect_to_sageodata(service_name=env)
    types = []
    if unit_no:
        types.append("unit_no")
    if obs_no:
        types.append("obs_no")
    if dh_no:
        types.append("dh_no")
    if singular_search_only:
        # Try and search dh_no only if there is no result
        df = db.find_wells(query, types=[t for t in types if not t == "dh_no"])
        if len(df) == 0:
            df = db.find_wells(query, types=types)
    else:
        df = db.find_wells(query, types=types)
    dh_nos = [int(dh_no) for dh_no in df.dh_no]
    url_str = webapp_utils.dhnos_to_urlstr(dh_nos)
    return {"dh_nos": dh_nos, "url_str": url_str}


@router.get("/utils_dhnos_to_urlstr", tags=["utils"])
def dhnos_to_urlstr(
    request: Request,
    dh_no: Annotated[list[int], Query()],
):
    return {"dh_nos": dh_no, "url_str": webapp_utils.dhnos_to_urlstr(dh_no)}


@router.get("/wells_summary", tags=["data"])
def wells_summary(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    well = db.wells_summary(dh_nos)
    return apply_format(
        well, format=format, response_name=f"wells_summary__{name_safe}"
    )


@router.get("/wells_manual_water_level", tags=["data"])
def manual_water_level(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.water_levels(dh_nos).sort_values("obs_date", ascending=False)
    return apply_format(
        df, format=format, response_name=f"manual_water_level__{name_safe}"
    )


@router.get("/wells_salinity", tags=["data"])
def salinity(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.salinities(dh_nos).sort_values("collected_date", ascending=False)
    return apply_format(df, format=format, response_name=f"wells_salinity__{name_safe}")


@router.get("/wells_drillhole_logs", tags=["data"])
def drillhole_logs(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    logs = db.drillhole_logs(dh_nos).sort_values("log_date", ascending=True)
    return apply_format(
        logs, format=format, response_name=f"wells_drillhole_logs__{name_safe}"
    )


@router.get("/wells_drillers_logs", tags=["data"])
def drillers_logs(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    drill = db.drillers_logs(dh_nos)
    return apply_format(
        drill, format=format, response_name=f"wells_drillers_logs__{name_safe}"
    )


@router.get("/wells_lith_logs", tags=["data"])
def lith_logs(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    lith = db.lith_logs(dh_nos)
    return apply_format(
        lith, format=format, response_name=f"wells_lith_logs__{name_safe}"
    )


@router.get("/wells_strat_logs", tags=["data"])
def strat_logs(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    strat = db.strat_logs(dh_nos)
    return apply_format(
        strat, format=format, response_name=f"wells_strat_logs__{name_safe}"
    )


@router.get("/wells_hydrostrat_logs", tags=["data"])
def hydrostrat_logs(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.hydrostrat_logs(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_hydrostrat_logs__{name_safe}"
    )


@router.get("/wells_construction_events", tags=["data"])
def construction_events(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.construction_events(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_construction_events__{name_safe}"
    )


@router.get("/wells_drilled_intervals", tags=["data"])
def drilled_intervals(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.drilled_intervals(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_drilled_intervals__{name_safe}"
    )


@router.get("/wells_casing_strings", tags=["data"])
def casing_strings(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.casing_strings(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_casing_strings__{name_safe}"
    )


@router.get("/wells_casing_seals", tags=["data"])
def casing_seals(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.casing_seals(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_casing_seals{name_safe}"
    )


@router.get("/wells_production_zones", tags=["data"])
def production_zones(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.production_zones(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_production_zones__{name_safe}"
    )


@router.get("/wells_other_construction_items", tags=["data"])
def other_construction_items(
    query: query_models.Wells = Depends(), format: str = "json"
):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.other_construction_items(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"wells_other_construction_items__{name_safe}",
    )


@router.get("/wells_water_cuts", tags=["data"])
def water_cuts(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.water_cuts(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_water_cuts__{name_safe}"
    )


@router.get("/wells_permits_by_completed_drillholes_only", tags=["data"])
def permits_by_completed_drillholes_only(
    query: query_models.Wells = Depends(), format: str = "json"
):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.permits_by_completed_drillholes_only(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"wells_permits_by_completed_drillholes_only__{name_safe}",
    )


@router.get("/wells_permit_conditions_and_notes", tags=["data"])
def permit_conditions_and_notes(
    query: query_models.Wells = Depends(), format: str = "json"
):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    p = db.permits_by_completed_drillholes_only(dh_nos)
    df = db.permit_conditions_and_notes(p.permit_no_only)
    return apply_format(
        df,
        format=format,
        response_name=f"wells_permit_conditions_and_notes__{name_safe}",
    )


@router.get("/wells_logger_data_summary", tags=["data"])
def logger_data_summary(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.logger_data_summary(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_logger_data_summary__{name_safe}"
    )


@router.get("/wells_logger_data_by_dh", tags=["data"])
def logger_data_by_dh(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.logger_data_by_dh(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_logger_data_by_dh__{name_safe}"
    )


@router.get("/wells_logger_wl_data_by_dh", tags=["data"])
def logger_wl_data_by_dh(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.logger_wl_data_by_dh(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_logger_wl_data_by_dh__{name_safe}"
    )


@router.get("/wells_geophys_log_metadata", tags=["data"])
def geophys_log_metadata(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    print(f"dh_nos: {dh_nos}")
    df = db.geophys_log_metadata(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_geophys_log_metadata__{name_safe}"
    )


@router.get("/wells_geophys_log_files", tags=["data"])
def geophys_log_files(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    print(f"dh_nos: {dh_nos}")
    df = db.geophys_log_files(dh_nos)
    return apply_format(
        df, format=format, response_name=f"wells_geophys_log_files__{name_safe}"
    )


@router.get("/wells_drillhole_document_image_list", tags=["data"])
def drillhole_document_image_list(
    query: query_models.Wells = Depends(), format: str = "json"
):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.drillhole_document_image_list(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"wells_drillhole_document_image_list__{name_safe}",
    )


@router.get("/wells_drillhole_notes", tags=["data"])
def drillhole_notes(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.drillhole_notes(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"drillhole_notes__{name_safe}",
    )


@router.get("/wells_drillhole_statuses", tags=["data"])
def drillhole_statuses(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.drillhole_status(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"drillhole_statuses__{name_safe}",
    )


@router.get("/wells_aquifers_monitored", tags=["data"])
def aquifers_monitored(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.aquifers_monitored(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"aquifers_monitored__{name_safe}",
    )


@router.get("/wells_elevation_surveys", tags=["data"])
def elevation_surveys(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.elevation_surveys(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"elevation_surveys__{name_safe}",
    )


@router.get("/wells_drillhole_file_list", tags=["data"])
def drillhole_file_list(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.drillhole_file_list(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"drillhole_file_list__{name_safe}",
    )


@router.get("/wells_usage", tags=["data"])
def usage(query: query_models.Wells = Depends(), format: str = "json"):
    db = gd.ExtractionInjectionDatabase()
    sagd_db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    sm = sagd_db.wells_summary(dh_nos)
    df = db.query_usage_for_drillholes(dh_nos)
    df2 = pd.merge(
        df,
        sm[["dh_no", "unit_hyphen", "latitude", "longitude"]],
        on="unit_hyphen",
        how="left",
    )
    return apply_format(
        df2,
        format=format,
        response_name=f"usage_kl__{name_safe}",
    )


@router.get("/wells_data_available", tags=["data"])
def data_available(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    df = db.data_available(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"wells_data_available__{name_safe}",
    )


@router.get("/db_file", tags=["data"], response_class=Response)
def db_file(
    file_no: int,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    file_name, stream = db.open_db_file(file_no)
    data = stream.read()
    if file_name.lower().endswith("pdf"):
        media_type = "application/pdf"
    elif file_name.lower().endswith("docx") or file_name.lower().endswith("doc"):
        media_type = "application/msword"
    elif file_name.lower()[-3:] in ("gif", "png", "bmp", "jpg"):
        media_type = f"image/{file_name.lower()[-3:]}"
    else:
        media_type = "application/octet-stream"
    response = Response(content=data, media_type=media_type)
    response.headers["Content-Disposition"] = (
        f"attachment; filename={file_no}_{file_name}"
    )
    return response


@router.get("/well_geophysical_log_file", tags=["data"], response_class=Response)
def well_geophysical_log_file(
    job_no: int,
    filename: str,
    env: str = "prod",
):
    job_path = gd.find_job_folder(job_no)
    file_path = job_path / filename
    with open(file_path, "rb") as f:
        data = f.read()
    if filename.lower().endswith("pdf"):
        media_type = "application/pdf"
    elif filename.lower().endswith("docx") or filename.lower().endswith("doc"):
        media_type = "application/msword"
    elif filename.lower()[-3:] in ("gif", "png", "bmp", "jpg"):
        media_type = f"image/{filename.lower()[-3:]}"
    elif (
        filename.lower().endswith("mp4")
        or filename.lower().endswith("mpg")
        or filename.lower().endswith("mpeg")
    ):
        media_type = f"video/mp4"
    elif filename.lower().endswith("vob"):
        media_type = f"video/MPV"
    else:
        media_type = "application/octet-stream"
    response = Response(content=data, media_type=media_type)
    response.headers["Content-Disposition"] = (
        f"attachment; filename={job_no}_{filename}"
    )
    return response


@router.get("/well_geophysical_las_file_data", tags=["data"], response_class=Response)
def well_geophysical_las_file_data(
    job_no: int,
    filename: str,
    format: str = "csv",
):
    job_path = gd.find_job_folder(job_no)
    file_path = job_path / filename
    if filename.lower().endswith("las"):
        las = lasio.read(file_path)
    buffer = io.StringIO()
    las.to_csv(buffer, units_loc="()")
    buffer.seek(0)
    data = buffer.read()
    response = Response(content=data, media_type="text/plain")
    response.headers["Content-Disposition"] = (
        f"attachment; filename={job_no}_{filename}.csv"
    )
    return response


@router.get("/drillhole_document_image", tags=["data"], response_class=Response)
def drillhole_document_image(
    image_no: int,
    rotation: int = 0,
    width: int = -1,
    height: int = -1,
    inline: bool = False,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    image = db.open_drillhole_document_image(image_no)
    image = gd.resize_image(image, width=width, height=height)
    image = image.rotate(-1 * rotation, expand=True, resample=Image.Resampling.BILINEAR)
    memfile = io.BytesIO()
    image.save(memfile, "PNG", quality=100)
    memfile.seek(0)
    data = memfile.read()
    if inline:
        data_base64 = base64.b64encode(data)  # encode to base64 (bytes)
        data_base64 = data_base64.decode()
        img_data = '<img src="data:image/jpeg;base64,' + data_base64 + '">'
        response = Response(content=f"<html>{img_data}</html>", media_type="text/html")
    else:
        response = Response(content=data, media_type="image/png")
        response.headers["Content-Disposition"] = (
            f"attachment; filename=drillhole_document_image_{image_no}.png"
        )
    return response


@router.get("/drillhole_image", tags=["data"], response_class=Response)
def drillhole_image(
    image_no: int,
    width: int = -1,
    height: int = -1,
    inline: bool = False,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    image = db.open_drillhole_image(image_no)
    image = gd.resize_image(image, width=width, height=height)
    memfile = io.BytesIO()
    image.save(memfile, "PNG", quality=100)
    memfile.seek(0)
    data = memfile.read()
    if inline:
        data_base64 = base64.b64encode(data)  # encode to base64 (bytes)
        data_base64 = data_base64.decode()
        img_data = '<img src="data:image/jpeg;base64,' + data_base64 + '">'
        response = Response(content=f"<html>{img_data}</html>", media_type="text/html")
    else:
        response = Response(content=data, media_type="image/png")
        response.headers["Content-Disposition"] = (
            f"attachment; filename=drillhole_image_{image_no}.png"
        )
    return response


@router.get("/drillhole_images", tags=["data"], response_class=Response)
def drillhole_images(
    dh_no: int,
    width: int = -1,
    height: int = -1,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    wells = db.drillhole_details([dh_no])
    well_id = wells.iloc[0].unit_hyphen
    if not well_id:
        well_id = str(dh_no)

    images = db.drillhole_image_list([dh_no])
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"dhimages_{well_id}_n{len(images)}_{timestamp}"

    fn = gd.produce_photo_zip(
        name,
        images,
    )
    with open(fn, mode="rb") as f:
        data = f.read()
    os.remove(fn)

    response = Response(content=data, media_type="application/zip")
    response.headers["Content-Disposition"] = f"attachment; filename={name}.zip"
    return response


@router.get("/drillhole_docimages", tags=["data"], response_class=Response)
def drillhole_docimages(
    dh_no: int,
    width: int = -1,
    height: int = -1,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    wells = db.drillhole_details([dh_no])
    well_id = wells.iloc[0].unit_hyphen
    if not well_id:
        well_id = str(dh_no)

    images = db.drillhole_document_image_list([dh_no])
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"dhdocimages_{well_id}_n{len(images)}_{timestamp}"

    fn = gd.produce_docimage_zip(
        name,
        images,
    )
    with open(fn, mode="rb") as f:
        data = f.read()
    os.remove(fn)

    response = Response(content=data, media_type="application/zip")
    response.headers["Content-Disposition"] = f"attachment; filename={name}.zip"
    return response


@router.get("/drillhole_geophysical_log_files", tags=["data"], response_class=Response)
def drillhole_geophysical_log_files(
    dh_no: int,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    md = db.geophys_log_metadata([dh_no])
    files = gd.list_geophys_job_files(job_nos=md.job_no.unique())

    well_id = md.iloc[0].unit_hyphen
    if not well_id:
        well_id = f"{dh_no}"

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"gl_files_{well_id}_n{len(files)}_{timestamp}"

    fn = gd.produce_geophysical_log_files_zip(
        name,
        files,
        exclude_extensions=("tif", "tiff", "mp4", "mpg", "mpeg", "avi", "vob"),
    )
    with open(fn, mode="rb") as f:
        data = f.read()
    os.remove(fn)

    response = Response(content=data, media_type="application/zip")
    response.headers["Content-Disposition"] = f"attachment; filename={name}.zip"
    return response


@router.get("/geophysical_logging_job_files", tags=["data"], response_class=Response)
def geophysical_logging_job_files(
    job_no: int,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    files = gd.list_geophys_job_files(job_nos=[job_no])

    id_str = f"Job_{job_no}"
    md = geophys_log_metadata_by_job_no([job_no])
    well_id = md.iloc[0].unit_hyphen
    if well_id:
        id_str += f"_{well_id}"

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"gl_files_{id_str}_n{len(files)}_{timestamp}"

    fn = gd.produce_geophysical_log_files_zip(
        name,
        files,
        exclude_extensions=("tif", "tiff", "mp4", "mpg", "mpeg", "avi", "vob"),
    )
    with open(fn, mode="rb") as f:
        data = f.read()
    os.remove(fn)

    response = Response(content=data, media_type="application/zip")
    response.headers["Content-Disposition"] = f"attachment; filename={name}.zip"
    return response


@router.get("/well_auto_dwcr", tags=["data"], response_class=Response)
def well_auto_dwcr(
    dh_no: int,
    completion_no: int,
    env: str = "prod",
):
    db = connect_to_sageodata(service_name=env)
    df = db.wells_summary([dh_no])
    unit_hyphen = df.iloc[0].unit_hyphen
    fn = f"AutoDWCR__{unit_hyphen}__{completion_no}.pdf"
    buffer = io.BytesIO()
    gd.auto_dwcr(buffer, dh_no, completion_no, db)
    buffer.seek(0)
    data = buffer.read()
    response = Response(content=data, media_type="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename={fn}"
    return response


@router.get("/well_best_available_logger_data", tags=["data"])
def well_best_available_logger_data(
    unit_hyphen: str,
    param: str = "swl",
    freq: str = "6H",
    keep_grades: str = "1, 20, 30",
    max_gap_days: float = 1,
    start: str = "",
    finish: str = "",
    aqts_env: str = "prod",
    format: str = "json",
):
    if not start:
        start = None
        start_str = ""
    else:
        start = gd.timestamp_acst(start)
        start_str = start.strftime("%Y-%m-%d")

    if not finish:
        finish = None
        finish_str = ""
    else:
        finish = gd.timestamp_acst(finish)
        finish_str = finish.strftime("%Y-%m-%d")

    keep_grades = [int(g) for g in keep_grades.split(",")] if keep_grades else []

    aq = gd.DEWAquarius(env=aqts_env)
    dfs = aq.fetch_timeseries_data(
        unit_hyphen,
        param=param,
        freq=freq,
        max_gap_days=max_gap_days,
        start=start,
        finish=finish,
        keep_grades=keep_grades,
    )
    df = gd.join_logger_data_intervals(dfs)
    df = df.drop(["index"], axis=1)
    df["timestamp"] = df.timestamp.dt.tz_localize(None)

    return apply_format(
        df,
        format=format,
        response_name=f"well_BA_logger__{unit_hyphen}_{param}_{freq}",
    )


@router.get("/well_best_available_combined_water_level_data", tags=["data"])
def well_best_available_combined_water_level_data(
    query: query_models.Wells = Depends(),
    param: str = "swl",
    freq: str = "5d",
    keep_grades: str = "1, 20, 30",
    max_gap_days: float = 550,
    start: str = "",
    finish: str = "",
    env: str = "prod",
    aqts_env: str = "prod",
    format: str = "json",
):
    if not start:
        start = None
        start_str = ""
    else:
        start = gd.timestamp_acst(start)
        start_str = start.strftime("%Y-%m-%d")

    if not finish:
        finish = None
        finish_str = ""
    else:
        finish = gd.timestamp_acst(finish)
        finish_str = finish.strftime("%Y-%m-%d")

    keep_grades = [int(g) for g in keep_grades.split(",")] if keep_grades else []

    aq = gd.DEWAquarius(env=aqts_env)
    db = connect_to_sageodata(service_name=env)

    dh_nos, name, name_safe, query_params = query.find_wells()

    dfs = gd.get_combined_water_level_dataset(
        dh_nos,
        db=db,
        param=param,
        freq=freq,
        start=start,
        finish=finish,
        max_gap_days=max_gap_days,
        keep_grades=keep_grades,
        aq_env=aqts_env,
    )
    df = gd.join_logger_data_intervals(dfs)
    df = df.drop(["index"], axis=1)
    df["timestamp"] = df.timestamp.dt.tz_localize(None)
    df = df.replace("null", np.nan)

    return apply_format(
        df,
        format=format,
        response_name=f"well_BA_comb_wl__{name_safe}_{param}_{freq}",
    )


@router.get("/query_swims_metadata", tags=["data"])
def query_swims_metadata(
    sql_query: str,
    format: str = "json",
):
    swimsmd = gd.SWIMSMetadata(use_api=False)
    df = swimsmd.query(sql_query)

    return apply_format(
        df,
        format=format,
        response_name=f"query_swims_metadata",
    )


@router.get("/wells_aqts_datasets", tags=["data"])
def wells_aqts_datasets(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    swimsmd = gd.SWIMSMetadata()

    dh_nos, name, name_safe, query_params = query.find_wells()
    dsets = swimsmd.datasets(dh_nos)
    return apply_format(
        dsets,
        format=format,
        response_name=f"wells_aqts_datasets__{name_safe}",
    )


@router.get("/query_wde_extended", tags=["data"])
def query_wde_extended(
    sql_query: str,
    format: str = "json",
):
    wde = gd.WDEExtended(use_api=False, fallback_to_api=False)
    df = wde.query(sql_query)

    return apply_format(
        df,
        format=format,
        response_name=f"query_wde_extended",
    )


@router.get("/wells_wde_logger_installations", tags=["data"])
def wde_logger_installations(
    query: query_models.Wells = Depends(), format: str = "json"
):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    wde = gd.WDEExtended()
    df = wde.logger_installations(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"logger_installations__{name_safe}",
    )


@router.get("/wells_wde_logger_readings", tags=["data"])
def wde_logger_readings(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    wde = gd.WDEExtended()
    df = wde.logger_readings(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"logger_readings__{name_safe}",
    )


@router.get("/wells_wde_maintenance_issues", tags=["data"])
def wde_maintenance_issues(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    wde = gd.WDEExtended()
    df = wde.maintenance_issues(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"maintenance_issues__{name_safe}",
    )


@router.get("/wells_wde_alerts", tags=["data"])
def wde_alerts(query: query_models.Wells = Depends(), format: str = "json"):
    db = connect_to_sageodata(service_name=query.env)
    dh_nos, name, name_safe, query_params = query.find_wells()
    wde = gd.WDEExtended()
    df = wde.wde_alerts(dh_nos)
    return apply_format(
        df,
        format=format,
        response_name=f"wde_alerts__{name_safe}",
    )


@router.get("/aquifer_database_file", tags=["data"], response_class=Response)
def aquifer_database_file(
    filename: str,
):
    aquifer_db = Path(
        r"r:\dfw_cbd\projects\projects_gw\state\groundwater_toolbox\aquifer_database"
    )
    file_path = aquifer_db / filename
    with open(file_path, "rb") as f:
        data = f.read()
    if filename.lower().endswith("pdf"):
        media_type = "application/pdf"
    elif filename.lower().endswith("docx") or filename.lower().endswith("doc"):
        media_type = "application/msword"
    elif filename.lower()[-3:] in ("gif", "png", "bmp", "jpg"):
        media_type = f"image/{filename.lower()[-3:]}"
    elif (
        filename.lower().endswith("mp4")
        or filename.lower().endswith("mpg")
        or filename.lower().endswith("mpeg")
    ):
        media_type = f"video/mp4"
    elif filename.lower().endswith("vob"):
        media_type = f"video/MPV"
    else:
        media_type = "application/octet-stream"
    response = Response(content=data, media_type=media_type)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.get("/all_drillholes", tags=["data"])
def all_drillholes(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.all_drillholes()
    return apply_format(
        df,
        format=format,
        response_name=f"all_drillholes",
    )


@router.get("/all_replacement_drillholes", tags=["data"])
def all_replacement_drillholes(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.all_replacement_drillholes()
    return apply_format(
        df,
        format=format,
        response_name=f"all_replacement_drillholes",
    )


@router.get("/all_aquifer_units", tags=["data"])
def all_aquifer_units(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.all_aquifer_units()
    return apply_format(
        df,
        format=format,
        response_name=f"all_aquifer_units",
    )


@router.get("/all_strat_units", tags=["data"])
def all_strat_units(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.all_strat_units()
    return apply_format(
        df,
        format=format,
        response_name=f"all_strat_units",
    )


@router.get("/all_mound_springs", tags=["data"])
def all_mound_springs(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.all_mound_springs()
    return apply_format(
        df,
        format=format,
        response_name=f"all_mound_springs",
    )


@router.get("/all_mound_spring_conditions", tags=["data"])
def all_mound_spring_conditions(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.all_mound_spring_conditions()
    return apply_format(
        df,
        format=format,
        response_name=f"all_mound_spring_conditions",
    )


@router.get("/monitoring_networks", tags=["data"])
def monitoring_networks(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.monitoring_networks()
    return apply_format(
        df,
        format=format,
        response_name=f"monitoring_networks",
    )


@router.get("/project_groups", tags=["data"])
def project_groups(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.project_groups()
    return apply_format(
        df,
        format=format,
        response_name=f"project_groups",
    )


@router.get("/chem_codes", tags=["data"])
def chem_codes(env: str = "prod", format: str = "json"):
    db = connect_to_sageodata(service_name=env)
    df = db.chem_codes()
    return apply_format(
        df,
        format=format,
        response_name=f"chem_codes",
    )
