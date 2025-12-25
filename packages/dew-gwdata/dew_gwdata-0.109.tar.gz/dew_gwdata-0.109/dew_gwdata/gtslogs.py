import collections
import glob
import os
import logging
from pathlib import Path
import pickle
import re
import shutil
import tempfile
import zipfile

import pandas as pd
import lasio

try:
    from pandas.core.groupby.groupby import DataError
except ImportError:
    from pandas.core.groupby import DataError

from . import utils

logger = logging.getLogger(__name__)

GTSLOGS_PATHS = {
    "sharedrive": Path(
        r"R:\DFW_CBD\ShareData\Corporate Science Information\Science Monitoring Information\Resource Monitoring Services\3 Assets & Services\Geophysics Glenside\Logging\Gtslogs"
    ),
    "geophyslogs": Path(r"R:\DFW_CBD\Geophyslogs\gtslogs"),
}


scanned_pdf = re.compile(r"\d*_dis[ck]\d*_.*")

_las_to_log_type_alias_mapping = (
    pd.read_csv(Path(__file__).parent / "las_to_alias.csv")
    .set_index("las_mnemonic")
    .alias_name
)


def las_to_log_type(mnemonic):
    """Convert LAS file mnemonic to a log type.

    Args:
        mnemonic (str)

    Returns:
        str: a log type alias. '?' is used for missing mnemonics.

    The mapping is stored in the file las_to_alias.csv which is stored along
    the dew_gwdata source files. Obviously, one day, it should be in SA Geodata.

    """
    if mnemonic in _las_to_log_type_alias_mapping.index.values:
        return _las_to_log_type_alias_mapping.loc[mnemonic]
    else:
        return "?"


def get_las_metadata(las_fn=None, las=None):
    """Quickly obtain some useful metadata about a LAS file.

    Args:
        las_fn (str): path to a LAS file, or LAS file contents as a string.
        las (LASFile object): can be used directly if available.

    Returns:
        dict: dictionary with keys:
          - "max_depth_las" (float) showing the actual range of depths
            in the file
          - "log_types" (str): comma-separated list of alphabetically sorted
            log_types from the mnemonics list below, excluding '?' and duplicates
          - "mnemonics" (list of dicts) - each item is a dict with keys
            "log_type", "las_mnemonic", and "extra_copy"

    """
    results = {}
    if las is None or las_fn is not None:
        las = lasio.read(
            las_fn, null_policy="none", ignore_header_errors=True, ignore_data=True
        )
    result = {}
    try:
        result["max_depth_las"] = max([las.well.STOP.value, las.well.STRT.value])
    except:
        result["max_depth_las"] = pd.NA
    result["mnemonics"] = las_curves_to_curve_records(las.curves.keys())
    log_types = [
        c["log_type"]
        for c in result["mnemonics"]
        if c["log_type"] != "?" and c["extra_copy"] is False
    ]
    result["log_types"] = ", ".join(sorted(list(set(log_types))))
    return result


def las_curves_to_curve_records(curves):
    """Convert LAS mnemonics to LAS curve records (dictionaries).

    Args:
        curves (sequence of str): mnemonics from a LAS file as read by lasio e.g.
            might include "GAMM:1" and "GAMM:2".

    Returns:
        list of dict. Each dict has keys:
          - "log_type": str showing the type of mnemonic/curve/tool
          - "las_mnemonic": the original mnemonic as supplied, but without the
            duplicate numbering so "GAMM:1" would become "GAMM" here.
          - "extra_copy": indicates if a curve was duplicated, so "GAMM:1" and
            "GAMM:2" would be extra_copy = True, whereas others would be False.

    The mapping from  LAS mnemonic to LAS log type is stored in
    the file las_to_alias.csv which is stored along
    the dew_gwdata source files. Obviously, one day, it should be in SA Geodata.

    """
    records = []
    for curve in curves:
        las_mnemonic = curve.split(":", 1)[0]
        record = {
            "log_type": las_to_log_type(las_mnemonic),
            "las_mnemonic": las_mnemonic,
            "extra_copy": (las_mnemonic != curve) & (not curve.endswith(":1")),
        }
        records.append(record)
    return records


def list_geophys_job_files(
    job_nos=None,
    job_paths=None,
    add_las_metadata=False,
    add_scan_metadata=True,
    sageodata_conn=None,
):
    """Obtain a listing of geophysical log files.

    Args:
        job_nos (sequence of int): geophysical logging job numbers to retrieve files for
        job_paths (sequence of str): folders to look in. Note that if
            sageodata_conn is None, this argument is ignored.
        add_las_metadata (bool): add LAS metadata fields to the dataframe
            which is returned. The fields come from the :func:`get_las_metadata`
            function, and the fields which are added are:

            - "max_depth_las": the maximum depth indicated by the LAS file header
              fields "STOP" and "START"
            - "log_types": comma-separated list of LAS log types (sorted alphabetically)
            - "mnemonics": comma-separated list of LAS mnemonics in the order found
              in the LAS file.
        add_scan_metadata (bool): add metadata for scanned analog log files. The data
            comes from the :func:`get_scan_metadata` function, and the only new
            field which is added is the "log_types" field (a comma-separated list of
            LAS log types, sorted alphabetically).
        sageodata_conn (SAGeodataConnection or None/False): if supplied, the file
            listing is obtained from the database, and the "path" field in the
            returned dataframe contains, instead of a path to a file, "sagd:file_no=XXX"
            where XXX is the primary key of the file record in the FI_FILE table.

    Returns:
        pd.DataFrame: a table with these columns:
          - job_no (int)
          - path (str): either a file path & filename, or sagd:file_no=XXX description
          - filename (str): the filename alone
          - file_type (str): uppercase file suffix

    """
    if sageodata_conn is None:
        df = _list_geophys_job_files_from_gtslogs(job_nos=job_nos, job_paths=job_paths)
    else:
        df = sageodata_conn.list_geophys_log_db_files(list(job_nos))

    def apply_las_metadata(row):
        if Path(row.path).is_file() and row.file_type == "LAS":
            las_md = get_las_metadata(row.path)
        elif str(row.path).startswith("sagd:file_no=") and row.file_type == "LAS":
            file_no = int(row.path.replace("sagd:file_no=", ""))
            fn, contents = sageodata_conn.open_db_file_as_text(file_no)
            if contents:
                las_md = get_las_metadata(contents)
            else:
                logger.warning(f"Error getting LAS file metadata for {row.path}")
                las_md = None
        else:
            las_md = None

        if las_md:
            row["max_depth_las"] = las_md["max_depth_las"]
            row["log_types"] = las_md["log_types"]
            row["mnemonics"] = ", ".join(
                [r["las_mnemonic"] for r in las_md["mnemonics"]]
            )
        else:
            row["max_depth_las"] = pd.NA
            row["log_types"] = ""
            row["mnemonics"] = ""

        return row

    def apply_scan_metadata(row):
        if Path(row.path).is_file() and row.file_type in ("TIF", "PDF"):
            md = get_scan_metadata(row.path)
            if md:
                row["max_depth_las"] = pd.NA
                row["log_types"] = ", ".join(
                    sorted([d["log_type"] for d in md["mnemonics"]])
                )
                row["mnemonics"] = ""
                return row
        return row

    if add_las_metadata:
        df = df.apply(apply_las_metadata, axis=1)

    if add_scan_metadata:
        df = df.apply(apply_scan_metadata, axis=1)

    return df.reset_index()


def _list_geophys_job_files_from_gtslogs(job_nos=None, job_paths=None):
    """Use :func:`list_geophys_job_files` with sageodata_conn=False
    rather than using this function directly."""
    files_dfs = []
    if job_nos is None and job_paths is None:
        job_paths = []
    if job_paths is None:
        job_paths = []
        for job_no in job_nos:
            try:
                job_paths.append(find_job_folder(job_no))
            except KeyError:
                continue
    for folder in job_paths:
        files_df = []
        for path in folder.iterdir():
            if path.is_file():
                size = utils.get_pretty_file_size(path)
                suffix = path.suffix.lstrip(".").upper()
                record = {
                    "job_no": int(path.parent.name),
                    "path": path,
                    "filename": path.name,
                    "file_type": suffix,
                    "file_size": size,
                    "max_depth_las": pd.NA,
                    "log_types": "",
                    "mnemonics": "",
                }
                files_df.append(record)
        files_dfs.append(pd.DataFrame(files_df))
    files_dfs = [f for f in files_dfs if len(f) > 0]
    if len(files_dfs):
        return pd.concat(files_dfs)
    else:
        return pd.DataFrame(
            [],
            columns=[
                "job_no",
                "path",
                "filename",
                "file_type",
                "file_size",
                "max_depth_las",
                "log_types",
                "mnemonics",
            ],
        )


def get_scan_metadata(fn):
    """Determine some metadata about a scanned geophysical log (analog log).

    Args:
        fn (str): filename of a PDF or TIFF scan

    Results:
        a dictionary containing these keys:
          - "max_depth_las": pd.NA as it can't be determined.
          - "mnemonics": a list of dicts - each inner dict has the keys:
            - "log_type": log type as annotated by Don in the filename back in 2020
            - "las_mnemonic": empty string ""
            - "extra_copy": False

    """
    fn = Path(fn)
    result = {}

    try:
        parts = fn.stem.split("_")
        job = int(parts[0])
        disk_number = None
        mnemonics = []
        for p in parts:
            m = re.match(r"\d+ ?$", p)
            if m:
                seq_number = int(m.group())
            else:
                if "dis" in p:
                    m_disk = re.search(r"\d+", p)
                    if m_disk:
                        disk_number = m_disk.group()
                    else:
                        print(f"{fn.name} Disk has no number? {p}")
                else:
                    if " " in p:
                        print(f"{fn.name} Space in path part: {p}")
                    mnemonics.append(
                        {
                            "log_type": p,
                            "las_mnemonic": "",
                            "extra_copy": False,
                        }
                    )
    except:
        logger.warning(f"Error parsing metadata from filename {fn}")
        mnemonics = ""

    result["max_depth_las"] = pd.NA
    result["mnemonics"] = mnemonics
    return result


def find_parent_job_folder(job_no: int, root_folder=None):
    """Return the folder in which a geophysical job folder would exist;
    raise KeyError if it does not exist yet.

    Args:
        job_no (int)
        root_folder (str): optional, R:\dfw_cbd\geophyslogs\gtslogs by default

    Returns:
        pathlib.Path object.

    This function can be used to create new job folders by finding
    where it should be created.

    """
    job_no = int(job_no)
    if root_folder is None:
        root_folder = r"r:\dfw_cbd\geophyslogs\gtslogs"
    for path in Path(root_folder).iterdir():
        if path.is_dir():
            folder = path
            if folder.name.startswith("Jobs "):
                parts = folder.name.split()
                start_job = int(parts[1])
                end_job = int(parts[3])
                if job_no >= start_job and job_no <= end_job:
                    return path
    return KeyError(f"{job_no} does not have a parent folder yet under {root_folder}")


def find_job_folder(job_no: int, root_folder=None):
    """Return a geophysical job folder or raise KeyError if it does not exist.

    Args:
        job_no (int)
        root_folder (str): optional, R:\dfw_cbd\geophyslogs\gtslogs by default

    Returns:
        pathlib.Path object.

    """
    job_no = int(job_no)
    if root_folder is None:
        root_folder = r"r:\dfw_cbd\geophyslogs\gtslogs"
    job_parent_folder = find_parent_job_folder(job_no, root_folder=root_folder)
    for path in job_parent_folder.iterdir():
        if path.is_dir():
            if path.name == str(int(job_no)):
                return path
    raise KeyError(f"{job_no} not found under {root_folder}")


def iter_job_folders(root_folder=None):
    """Iterate through all existing geophysical job folders, yielding
    a pathlib.Path object on each iteration."""
    if root_folder is None:
        root_folder = r"r:\dfw_cbd\geophyslogs\gtslogs"
    for path in Path(root_folder).iterdir():
        if path.is_dir():
            folder = path
            if folder.name.startswith("Jobs "):
                for sub_path in folder.iterdir():
                    try:
                        job_no = int(sub_path.name)
                    except:
                        pass
                    else:
                        yield sub_path


class GtslogsArchiveFolder:
    """Archive of gtslogs data.

    Args:
        path (str): `'geophyslogs'`, `'sharedrive'`, or a path to a folder.

    """

    pickle_filename = "dew_gwdata_cache.pickle"

    def __init__(
        self,
        path="geophyslogs",
        generate_cache=False,
        include_confidential=True,
        **kwargs,
    ):
        try:
            from dew_gwdata.sageodata.oracledb import connect

            self.db = connect()
        except:
            self.db = None

        if not os.path.isdir(path):
            path = GTSLOGS_PATHS[path]

        self.path = Path(path)
        self._job_paths = {}
        self._job_ranges = {}
        if generate_cache:
            self.cache_job_paths()
        else:
            if os.path.isfile(self.pickle_path):
                self.load_job_path_cache()
            else:
                raise Warning("you need to run with generate_cache=True at least once")
        self.include_confidential = include_confidential
        self.job_kwargs = kwargs

    @property
    def include_confidential(self):
        return self._include_confidential

    @include_confidential.setter
    def include_confidential(self, value):
        self._include_confidential = value
        if value:
            self.included_jobs = self._job_paths.keys()
        else:
            if self.db:
                self.included_jobs = [
                    int(job)
                    for job in self.db.query(
                        "select job_no from dhdb.gl_log_hdr_vw where gl_confidential_flag = 'N'"
                    ).job_no.values
                    if not pd.isnull(job)
                ]
            else:
                print(
                    "Unable to filter out confidential jobs without access to SA Geodata."
                )
                self.included_jobs = self._job_paths.keys()

    @property
    def job_paths(self):
        return {
            job: path
            for job, path in self._job_paths.items()
            if job in self.included_jobs
        }

    @property
    def job_ranges(self):
        return self._job_ranges

    @property
    def pickle_path(self):
        return os.path.join(self.path, self.pickle_filename)

    def find_jobs_for_wells(self, wells):
        jobs = self.db.geophys_log_metadata(wells.dh_no)
        return self[sorted(jobs.job_no.tolist())]

    def refresh(self):
        return self.cache_job_paths()

    def cache_job_paths(self):
        self._job_paths = {}
        self._job_ranges = {}
        for job, path, dirs, filenames in self.walk():
            self._job_paths[job] = path
        self.save_job_path_cache()

    def save_job_path_cache(self):
        with open(self.pickle_path, "wb") as f:
            pickle.dump(
                {"_job_ranges": self._job_ranges, "_job_paths": self._job_paths}, f
            )

    def load_job_path_cache(self):
        with open(self.pickle_path, "rb") as f:
            self.__dict__.update(pickle.load(f))

    def __iter__(self):
        for job_no, job_path in self.job_paths.items():
            yield GLJob(job_path)

    def walk(self):
        """Iterate through Gtslogs.

        Arguments:
            - path (str): root path to search through. You can use a
                file path or a key to the module-level
                variables ``paths``.

        Return:
            A generator. Each next() method call returns a tuple
            ``(job, path, dirs, filenames)``

        Note that it won't iterate through files inside a subfolder of
        a job folder.

        """
        for path, dirs, filenames in os.walk(self.path, topdown=True):
            logger.debug(str(path))

            span = re.search(r"Jobs (\d+) to (\d+)$", path)
            if span:
                job_from = int(span.group(1))
                job_to = int(span.group(2))
                logger.info("{}-{} = {}".format(job_from, job_to, path))
                self._job_ranges[(job_from, job_to)] = path

            dirs.sort(reverse=True)
            base, name = os.path.split(path)
            try:
                job = int(name)
            except:
                pass
            else:
                yield job, path, dirs, filenames

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.job(key, create_if_necessary=False)
        else:
            return self.jobs(key, create_if_necessary=False)

    def job(self, job, create_if_necessary=True, **kwargs):
        """Open geophysical logging job.

        Args:
            job (int): job number.
            create_if_necessary (bool): create an empty folder if
                warranted.

        Other keyword arguments are passed the GLJob constructor.

        Returns: `dew_gwdata.GLJob` object.

        """
        kws = self.job_kwargs
        kws.update(kwargs)
        job = int(job)
        if job in self.job_paths:
            return GLJob(self.job_paths[job], **kws)
        else:
            logger.info("Unable to locate a folder for job {}".format(job))
            for job_from, job_to in self.job_ranges.keys():
                logger.debug(f"Checking for job {job} in range {job_from} to {job_to}")
                if job >= job_from and job <= job_to:
                    parent_path = self.job_ranges[(job_from, job_to)]
                    candidate_job_path = os.path.join(parent_path, str(job))
                    if not os.path.isdir(candidate_job_path):
                        if (
                            not os.path.isfile(candidate_job_path)
                            and create_if_necessary
                        ):
                            logger.info(
                                "Creating job folder {}".format(candidate_job_path)
                            )
                            os.makedirs(candidate_job_path)
                            self.job_paths[job] = candidate_job_path
                            self.save_job_path_cache()
                    if os.path.isdir(candidate_job_path):
                        return GLJob(candidate_job_path, **kws)
        raise KeyError("GLJob {} does not exist in this archive".format(job))

    def jobs(self, job_nos, **kwargs):
        """Return geophysical logging jobs.

        Args:
            job_nos (iterable): list of job numbers.

        Other keyword arguments will be passed to self.job().

        Returns: `dew_gwdata.GLJobs` object.

        """
        return GLJobs([self.job(job_no, **kwargs) for job_no in job_nos])

    def __repr__(self):
        return "<GtslogsArchiveFolder {} jobs @ {}...{}>".format(
            len(self.job_paths), self.path[:8], self.path[-25:]
        )


class GLJobs(collections.abc.MutableSequence):
    """A collection of geophysical logging jobs.

    Not meant to be initialised directly - use
    `dew_gwdata.GtslogsArchiveFolder.jobs()`
    method.

    """

    def __init__(self, jobs=None):
        if jobs is None:
            jobs = []
        self.jobs = jobs
        self._refresh()

    def __repr__(self):
        return repr(self.jobs)

    def __len__(self):
        return len(self.jobs)

    def __getitem__(self, ix):
        return self.jobs[ix]

    def __delitem__(self, ix):
        del self.jobs[ix]
        self._refresh()

    def __setitem__(self, ix, value):
        self.jobs[ix] = value

    def insert(self, ix, value):
        self.jobs.insert(ix, value)
        self._refresh()

    def append(self, value):
        self.jobs.append(value)
        self._refresh()

    def count(self, item):
        return self.jobs.count(item)

    def index(self, *args):
        return self.jobs.index(*args)

    def __iter__(self):
        return iter(self.jobs)

    def _refresh(self):
        if len(self):
            self._attributes = list(self[0].to_scalar_dict().keys())
        else:
            self._attributes = []

    def __getattr__(self, name):
        if name in self._attributes:
            return [getattr(j, name) for j in self]
        else:
            raise AttributeError(
                "GLJobs object does not have an attribute named '{}'".format(name)
            )

    def glob(self, pattern):
        results = []
        for job in self:
            results += job.glob(pattern)
        return results

    @property
    def filenames(self):
        return self.glob("*.*")

    @property
    def data_filenames(self):
        results = []
        for job in self:
            results += job.data_filenames
        return [Path(r) for r in results]

    @property
    def data_files(self):
        results = []
        for job in self:
            results += job.data_files
        return results

    def get_preferred_data_filenames(self, *args, **kwargs):
        return [job.get_preferred_data_filename(*args, **kwargs) for job in self]

    def get_preferred_data_files(self, *args, **kwargs):
        return [job.get_preferred_data_file(*args, **kwargs) for job in self]

    def geophys_log_metadata(self, conn=None, **kwargs):
        """Get geophysical log metadata from SA Geodata."""
        if conn is None:
            from dew_gwdata import sageodata

            conn = sageodata(**kwargs)
        return conn.geophys_log_metadata_by_job_no([j.number for j in self.jobs])


class GLJob:
    def __init__(
        self, path, preferred_files_regexp=".*", preferred_file_method="last_modified"
    ):
        assert preferred_file_method in (
            "last_modified",
            "largest",
            "shortest_filename",
        )
        self._preferred_files_regexp = preferred_files_regexp
        self._preferred_file_method = preferred_file_method
        self.number = int(os.path.split(path)[-1])
        self.job_no = self.number
        logger.debug("opening job {}".format(self.number))
        self.path = Path(path)

    def __hash__(self):
        return self.number

    def to_scalar_dict(self):
        return {
            "number": self.number,
            "job_no": self.job_no,
            "path": self.path,
            # "curves": self.curves,
        }

    def copy_files(self, destination, pattern="*.*"):
        for filename in self.glob(pattern):
            filename = Path(filename)
            shutil.copy(filename, destination)

    @property
    def curves(self):
        curves = []
        for f in self.data_files:
            curves += list(f.curves)
        return set(curves)

    def glob(self, pattern):
        return glob.glob(os.path.join(self.path, pattern))

    @property
    def filenames(self):
        return glob.glob(os.path.join(self.path, "*.*"))

    @classmethod
    def from_filename(cls, filename, **kwargs):
        """Given a filename, return the job number and file name."""
        path = Path(filename)
        job_path_parts = []
        found_job = False
        for part in path.parts[::-1]:
            if found_job:
                job_path_parts.append(part)
            else:
                try:
                    int(part)
                except:
                    pass
                else:
                    found_job = True
                    job_path_parts.append(part)
        return cls(os.path.join(*job_path_parts[::-1]), **kwargs)

    def _get_preferred_file(self, fns=None, method=None):
        if fns is None:
            fns = self.data_filenames
        if method is None:
            method = self._preferred_file_method
        if method == "last_modified":
            return sorted(fns, key=lambda x: os.path.getmtime(x))[-1]
        elif method == "largest":
            return sorted(fns, key=lambda x: os.path.getsize(x))[-1]
        elif method == "shortest_filename":
            return sorted(fns, key=len)[0]

    def get_preferred_data_filename(self, regexp=None):
        if regexp is None:
            regexp = self._preferred_files_regexp

        data_filenames = [
            fn for fn in self.data_filenames if re.search(regexp, os.path.basename(fn))
        ]
        n = len(data_filenames)
        if n == 0:
            return ""
        elif n == 1:
            return data_filenames[0]
        else:
            masters = [fn for fn in data_filenames if ".master" in fn.lower()]
            if len(masters) == 0:
                return self._get_preferred_file(data_filenames)
            elif len(masters) == 1:
                return masters[0]
            else:
                return self._get_preferred_file(masters)

    def get_preferred_data_file(self, **kwargs):
        return LogDataFile(self.get_preferred_data_filename(**kwargs))

    @property
    def data_filenames(self):
        filenames = []
        for fn in self.filenames:
            _, ext = os.path.splitext(fn)
            ext = ext.lower()[1:]
            logger.debug(
                "Checking to see whether {} is a supported log data file extension type".format(
                    ext
                )
            )
            if ext in LogDataFile.supported_exts:
                filenames.append(fn)
        return [Path(fn) for fn in filenames]

    @property
    def data_files(self):
        return [LogDataFile(fn) for fn in self.data_filenames]

    @property
    def scanned_log_pdfs(self):
        filenames = []
        for fn in Path(self.path).glob("*.pdf"):
            if scanned_pdf.match(fn.stem):
                filenames.append(fn)
        return [Path(fn) for fn in filenames]

    def dfs(self, include_curves=None, case_insensitive_match=True):
        """Return dataframes for log data files in job.

        Args:
            include_curves (list): list of regexps for curves to retain.
                if None, keep all.
            case_insensitive_match (bool): if True, make the regexp pattern
                matching case-insensitive

        Returns: dictionary of filename: dataframe selections.

        """
        if not include_curves:
            include_curves = ["*"]
        dfs = {}
        for f in self.data_files:
            df = f.df()
            cols = list(df.columns)
            keep_cols = []
            for col in cols:
                for pattern in include_curves:
                    if case_insensitive_match:
                        pattern = "(?i)" + pattern
                    if re.match(pattern, col) and not col in keep_cols:
                        keep_cols.append(col)
            dfs[f.filename] = df[keep_cols]
        return dfs

    def df(self):
        """Load all curves from all available data files.

        Returns: pandas DataFrame with a MultiIndex for columns
        with levels (filename and curve).

        This may or may not work! TODO FIX ME!

        # For example:

        #     >>> import dew_gwdata as gd
        #     >>> archive = gd.GtslogsArchiveFolder()
        #     >>> df = archive.job(9641).df()
        #     >>> df.info(max_cols=200)
        #     <class 'pandas.core.frame.DataFrame'>
        #     Float64Index: 39686 entries, -0.2103568750114324 to 234.98
        #     Data columns (total 108 columns):
        #     (allwaterNo4_cal8_down_CAL8_2018-12-18_084437.csv, v1 caliper arm extension)                 11650 non-null float64
        #     (allwaterNo4_cal8_down_CAL8_2018-12-18_084437.csv, diameter)                                 11650 non-null float64
        #     ...
        #     (rawdata_allwaterNo4_IND3S_up_IND3S_2018-12-18_114926.csv, depth_v1)                         4837 non-null float64
        #     (rawdata_allwaterNo4_IND3S_up_IND3S_2018-12-18_114926.csv, depth_apparent conductivity)      4837 non-null float64
        #     (rawdata_allwaterNo4_IND3S_up_IND3S_2018-12-18_114926.csv, apparent conductivity)            4837 non-null float64
        #     dtypes: float64(108)
        #     memory usage: 33.0 MB

        # For example, to select only the gamma logs:

        #     >>> gammas = df.iloc[:, df.columns.get_level_values("curve") == "gamma"]
        #     >>> gammas.info()
        #     <class 'pandas.core.frame.DataFrame'>
        #     Float64Index: 39686 entries, -0.2103568750114324 to 234.98
        #     Data columns (total 4 columns):
        #     (allwaterNo4_G9N9SP_down_G9N9+Box1_2018-12-18_104314.csv, gamma)            8700 non-null float64
        #     (allwaterNo4_G9N9SP_up_G9N9+Box1_2018-12-18_110124.csv, gamma)              8700 non-null float64
        #     (rawdata_allwaterNo4_G9N9SP_down_G9N9+Box1_2018-12-18_104314.csv, gamma)    3948 non-null float64
        #     (rawdata_allwaterNo4_G9N9SP_up_G9N9+Box1_2018-12-18_110124.csv, gamma)      6825 non-null float64
        #     dtypes: float64(4)
        #     memory usage: 1.5 MB

        """
        dfs = []
        columns = []
        for i, (fn, f) in enumerate(zip(self.data_filenames, self.data_files)):
            df = f.df()
            name = os.path.basename(fn)
            df.columns = pd.MultiIndex.from_tuples([(name, x) for x in df.columns])
            df.columns.names = ["filename", "curve"]
            dfs.append(df)
        if dfs:
            return pd.concat(dfs, axis=1).interpolate(method="slinear")
        else:
            return pd.DataFrame()

    def geophys_log_metadata(self, conn=None, **kwargs):
        """Get geophysical log metadata from SA Geodata."""
        if conn is None:
            from dew_gwdata import sageodata

            conn = sageodata(**kwargs)
        return conn.geophys_log_metadata_by_job_no([self.number])

    def __repr__(self):
        return "<GL GLJob {}: {} data files>".format(
            self.number, len(self.data_filenames)
        )

    def __int__(self):
        return self.number


def merge_dataframes(dfs, index_duplicate_agg="mean"):
    def get_keys(frames):
        all_keys = []
        for frame in frames:
            cols = list(frame)
            all_keys += cols
        return set(all_keys)

    def rename(frames):
        ret_frames = [list(keys) for keys in frames]
        for key in get_keys(frames):
            locations = []
            for i, frame in enumerate(frames):
                for j, test_key in enumerate(frame):
                    if test_key == key:
                        locations.append((i, j))
            if len(locations) > 1:
                current_count = 1
                for k, (i, j) in enumerate(locations):
                    test_key = frames[i][j]
                    ret_frames[i][j] = test_key + ":{:.0f}".format(k + 1)
        return ret_frames

    labels = [list(df.columns) for df in dfs]
    new_labels = rename(labels)
    new_dfs = []
    for i, df in enumerate(dfs):
        df.columns = new_labels[i]
        try:
            df = df.groupby(df.index).agg(index_duplicate_agg)
        except DataError:
            logger.warning("Skipping dataframe because it lacks numeric data.")
        else:
            new_dfs.append(df)

    if len(new_dfs):
        return pd.concat(new_dfs, axis=1)
    else:
        return pd.DataFrame()


class LogDataFile(object):
    supported_exts = set(("csv", "las"))

    def __init__(self, path, job=None, **kwargs):
        folder, filename = os.path.split(path)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()[1:]

        self._cached = None
        self.reload_kwargs = kwargs
        self.job = job
        self.path = path
        self.folder = folder
        self.filename = filename
        self.ext = ext

        if ext == "csv":
            self.__class__ = CSVLogDataFile
        elif ext == "las":
            self.__class__ = LASLogDataFile

    @property
    def dataobj(self):
        if self._cached is None:
            self._cached = self.reload()
        return self._cached

    def df(self):
        try:
            df = self.dataobj.df()
        except:
            df = self.dataobj
        df.columns = [k.strip().lower() for k in df.columns]
        return df

    @dataobj.setter
    def dataobj(self, value):
        raise NotImplementedError(
            "Cannot set data object directly - modify {} instead.".format(self.path)
        )


class CSVLogDataFile(LogDataFile):
    def df(self):
        return self.dataobj

    def reload(self):
        df = (
            pd.read_csv(self.path, skiprows=[1], **self.reload_kwargs)
            .rename(columns=lambda x: x.strip())
            .rename(columns=str.lower)
        )
        for key in df.columns:
            if key == "depth":
                df = df.set_index(key)
        # dfs = []
        # df_cols = list(df.columns)
        # for key in df_cols:
        #     if key in df.columns:
        #         if key == "depth_" and not key == "depth_original":
        #             data_key = key.replace("depth_", "")
        #             sub_df = pd.DataFrame(
        #                 {"depth": df[key], data_key: df[data_key]}
        #             ).set_index("depth")
        #             dfs.append(sub_df)
        #             df = df[[x for x in df.columns if not x in (key, data_key)]]
        # dfs.append(df.set_index("depth"))

        # new_df = merge_dataframes(dfs)
        # final_df = new_df.interpolate(method="slinear")
        self._cached = df
        return self._cached

    def depth_column(self, key=None):
        curves = self.curves()
        possible_depth_keys = ["Depth", "depth", curves[0]]
        if key:
            possible_depth_keys.insert(0, "depth_{}".format(key))
        for depth_key in possible_depth_keys:
            if depth_key in self.curves():
                break
        return depth_key

    @property
    def curves(self):
        return [x.strip().lower() for x in self.df().columns]

    def curve(self, key):
        return pd.Series(
            data=self.df()[key].values, index=self.df()[self.depth_column()].values
        ).dropna()


class LASLogDataFile(LogDataFile):
    def las(self):
        return self.dataobj

    def reload(self):
        self._cached = lasio.read(self.path, **self.reload_kwargs)
        return self._cached

    @property
    def curves(self, case_transform=None):
        """Get name of the available curves.

        Args:
            case_transform (func, optional): function to transform the
                curve name e.g. `lower`, `upper`. By default it is
                `lambda curve: curve`

        Returns: a list of the curve names for use with :meth:`LASLogDataFile.curve`.

        """
        return [x.strip() for x in self.las().keys()]

    def depth_column(self, key=None):
        return self.las().keys()[0]

    def curve(self, key):
        return pd.Series(data=self.las()[key], index=self.las().curves[0].data).dropna()


def check_las_file_for_candidate_curves(las_fn, candidate_curves, case_sensitive=False):
    """Check a LAS file to see if it has a particular type of
    log data based on the curve name(s).

    Args:
        las_fn (str): a LAS file
        candidate_curves (sequence): a list of curve names
            to look for
        case_sensitive (bool): default False

    Returns: boolean

    """
    las = lasio.read(las_fn, ignore_data=True)
    las_curves = [name for name in las.keys()]
    if not case_sensitive:
        las_curves = [name.lower() for name in las_curves]
        candidate_curves = [c.lower() for c in candidate_curves]
    matched_curves = [name for name in las_curves if name in candidate_curves]
    if len(matched_curves):
        return True
    else:
        return False


def produce_geophysical_log_files_zip(zfn_name, gl_files, exclude_extensions=None):
    """gl_files needs columns "job_no" and "file_name" """
    if exclude_extensions is None:
        exclude_extensions = []

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
