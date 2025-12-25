Water licensing data
====================

``dew_gwdata`` provides access, where possible, to Water Licensing databases relating
to our work in water science. e.g. usage volumes from bores, and allocations.

The relevant water licensing database was called WILMA up until its replacement
by mywater in 2024. There is currently no way to access usage or allocation data
from mywater (as of March 2025), so this page only refers to historical data from WILMA.

WILMA Reporting - usage and allocation data (2014-2024)
-------------------------------------------------------

WILMA had a reporting function which allowed us to query and export CSVs containing
usage and allocation data. I've stored these exports on the network folder and they
can be accessed readily using :func:`dew_gwdata.read_from_wilma_sqlite_db`:

.. code-block:: python

    >>> import dew_gwdata as gd
    >>> wilma = gd.read_from_wilma_sqlite_db()
    >>> wilma._fields
    ('alloc', 'usage', 'parcels')

``wilma``

    >>> wilma.usage.info()
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 89247 entries, 0 to 89246
    Data columns (total 26 columns):
    #   Column              Non-Null Count  Dtype
    ---  ------              --------------  -----
    0   index               89247 non-null  int64
    1   licence_no          89247 non-null  int64
    2   licence_seq         89247 non-null  int64
    3   wateraccnt          89247 non-null  object
    4   sua                 89247 non-null  int64
    5   source_id           89247 non-null  int64
    6   sourcedesc          89247 non-null  object
    7   meter_id            89247 non-null  object
    8   easting             89247 non-null  object
    9   northing            89247 non-null  object
    10  resource_type       89247 non-null  object
    11  resource_group      89247 non-null  object
    12  pres_area           89247 non-null  object
    13  year                89247 non-null  int64
    14  metered             89247 non-null  int64
    15  supplied1           89247 non-null  int64
    16  adjustment          89247 non-null  int64
    17  deemed              89247 non-null  int64
    18  effective           89247 non-null  int64
    19  levy_year           89247 non-null  int64
    20  source_unit_hyphen  89247 non-null  object
    21  downloaded          89247 non-null  object
    22  filename            89247 non-null  object
    23  unit_hyphen         89247 non-null  object
    24  latitude            89247 non-null  float64
    25  longitude           89247 non-null  float64
    dtypes: float64(2), int64(12), object(12)
    memory usage: 17.7+ MB

