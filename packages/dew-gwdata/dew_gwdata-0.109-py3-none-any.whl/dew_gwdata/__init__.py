import importlib.metadata

__version__ = importlib.metadata.version(__name__)

from .sageodata_database import *
from .sageodata_database import connect as connect_to_sageodata

sageodata = connect_to_sageodata

from .sageodata_datamart import get_sageodata_datamart_connection
from .wilma_reports import *
from .gtslogs import *
from .hydstra import *
from .aquarius_ts import *
from .aquarius_wp import *
from .wde import *
from .sagd_api import *
from .extraction_data import *
from .gwdata import *
from .utils import *
from .charts import *
from .package_database import *

register_aq_password("timeseries", "timeseries")
