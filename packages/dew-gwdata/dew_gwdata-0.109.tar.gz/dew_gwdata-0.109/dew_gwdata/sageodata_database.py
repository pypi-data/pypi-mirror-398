from pathlib import Path
import tempfile
import zipfile

import sageodata_db

from .utils import *


def connect(user="gwquery", password="gwquery", **kwargs):
    """Connect to SA Geodata.

    Args:
        user (str): oracle user
        password (str): password
        service_name (str): version of SA Geodata you would like to connect
            to - options are "DMED.WORLD" or "dev"; "DMET.WORLD" or "test" or
            "QA"; or "DMEP.WORLD" or "prod" - see
            :func:`sageodata_db.normalize_service_name` for details.

    Other keyword arguments are passed to
    :func:`sageodata_db.make_connection_string`.

    Returns: a :class:`sageodata_db.SAGeodataConnection` object.

    Example:

        >>> from dew_gwdata import sageodata
        >>> db = sageodata()
        >>> db
        <sageodata_db.connection.SAGeodataConnection to gwquery@pirsapd07.pirsa.sa.gov.au:1521/DMEP.World>

    """
    db = sageodata_db.connect(user=user, password=password, **kwargs)
    return db


def produce_photo_zip(zfn_name, images, width=-1, height=-1, env="prod"):
    from dew_gwdata import connect_to_sageodata

    db = connect_to_sageodata(service_name=env)

    zfn = str(Path(tempfile.gettempdir()) / (zfn_name + ".zip"))
    zfile = zipfile.ZipFile(zfn, mode="w")

    with tempfile.TemporaryDirectory() as tmp_path:
        path = Path(tmp_path)
        for idx, row in images.iterrows():
            image = db.open_drillhole_image(row.image_no)
            image = resize_image(image, width=width, height=height)

            image_date = "unk"
            if row.image_date:
                image_date = row.image_date.strftime("%Y-%m-%d")

            photographer = "unk"
            if row.photographer:
                photographer = row.photographer

            fn = (
                path
                / f"{row.image_no}_{image_date}_{photographer}_{row.original_filename}"
            )
            with open(fn, mode="wb") as f:
                image.save(f, "PNG", quality=100)

            zfile.write(fn, arcname=fn.name)

    return zfn


def produce_docimage_zip(zfn_name, images, width=-1, height=-1, env="prod"):
    from dew_gwdata import connect_to_sageodata

    db = connect_to_sageodata(service_name=env)

    zfn = str(Path(tempfile.gettempdir()) / (zfn_name + ".zip"))
    zfile = zipfile.ZipFile(zfn, mode="w")

    with tempfile.TemporaryDirectory() as tmp_path:
        path = Path(tmp_path)
        for idx, row in images.iterrows():
            image = db.open_drillhole_document_image(row.image_no)
            image = resize_image(image, width=width, height=height)

            fn = path / f"{row.image_no}_{row.document_type}_{row.filename}"
            with open(fn, mode="wb") as f:
                image.save(f, "PNG", quality=100)

            zfile.write(fn, arcname=fn.name, compress_type=zipfile.ZIP_DEFLATED)

    return zfn


def produce_geophysical_log_files_zip(zfn_name, gl_files, exclude_extensions=None):
    """gl_files needs columns "job_no" and "file_name" """
    if exclude_extensions is None:
        exclude_extensions = []
    from dew_gwdata import find_job_folder

    job_paths = {
        job_no: find_job_folder(job_no)
        for job_no in [j for j in gl_files.job_no.unique() if not pd.isnull(j)]
    }

    zfn = str(Path(tempfile.gettempdir()) / (zfn_name + ".zip"))
    zfile = zipfile.ZipFile(zfn, mode="w")

    with tempfile.TemporaryDirectory() as tmp_path:
        path = Path(tmp_path)
        for idx, row in gl_files.iterrows():
            path = Path(job_paths[row.job_no]) / row.filename
            do_not_write = False
            for excl in exclude_extensions:
                if row.filename.lower().endswith("." + excl.lower()):
                    do_not_write = True
            if not do_not_write:
                zfile.write(
                    str(path),
                    arcname=f"{row.job_no}/{row.filename}",
                    compress_type=zipfile.ZIP_DEFLATED,
                )

    return zfn
