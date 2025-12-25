Introduction
============

``dew_gwdata`` provides access to databases and applications containing groundwater data. 

The main ones are SA Geodata and a suite of Aquarius products from Aquatic Informatics. 
SA Geodata contains the majority of groundwater data. 
Aquarius products contain continuous water level and electrical conductivity (EC) logger data.

SA Geodata
----------------

SA Geodata is an enterprise Oracle database. You need to be on the SA Government intranet to access it. 

All of the functions that access SA Geodata require a connection, which you create quite easily using
:func:`dew_gwdata.sageodata`:

.. code-block:: python

    >>> import dew_gwdata as gd
    >>> db = gd.sageodata()
    >>> db
    <sageodata_db.connection.SAGeodataConnection to gwquery@pirsapd07.pirsa.sa.gov.au:1521/DMEP.WORLD>

This can be used to identify wells using :meth:`sageodata_db.SAGeodataConnection.find_wells`:

.. code-block:: python

    >>> wells = db.find_wells("CAR011 and KON 33 ")

This returns a ``pandas.DataFrame`` table (`10 min intro to pandas <https://pandas.pydata.org/docs/user_guide/10min.html>`_).

.. code-block:: python

    >>> wells.info()
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 2 entries, 0 to 1
    Data columns (total 71 columns):
    #   Column                     Non-Null Count  Dtype
    ---  ------                     --------------  -----
    0   well_id                    2 non-null      object
    1   dh_no                      2 non-null      int64
    2   unit_hyphen                2 non-null      object
    3   obs_no                     2 non-null      object
    4   dh_name                    2 non-null      object
    5   unit_long                  2 non-null      int64
    6   easting                    2 non-null      float64
    7   northing                   2 non-null      float64
    8   zone                       2 non-null      int64
    9   latitude                   2 non-null      float64
    10  longitude                  2 non-null      float64
    11  aquifer                    2 non-null      object
    12  pwa                        2 non-null      object
    13  pwra                       0 non-null      object
    14  nrm                        2 non-null      object
    15  landscape                  2 non-null      object
    16  dh_other_name              2 non-null      object
    17  parent_dh_no               0 non-null      object
    18  child_dh_no                0 non-null      object
    19  replaced_date              0 non-null      object
    20  latest_status              1 non-null      object
    21  latest_status_date         1 non-null      datetime64[ns]
    22  purpose                    2 non-null      object
    23  owner                      2 non-null      object
    24  orig_drilled_depth         1 non-null      float64
    25  orig_drilled_date          1 non-null      datetime64[ns]
    26  max_drilled_depth          2 non-null      float64
    27  max_drilled_depth_date     2 non-null      datetime64[ns]
    28  latest_open_depth          2 non-null      float64
    29  latest_open_depth_date     2 non-null      datetime64[ns]
    30  latest_cased_from          2 non-null      float64
    31  latest_cased_to            2 non-null      float64
    32  latest_casing_min_diam     2 non-null      int64
    33  drill_method               2 non-null      object
    34  comments                   1 non-null      object
    35  latest_dtw                 2 non-null      float64
    36  latest_swl                 2 non-null      float64
    37  latest_rswl                2 non-null      float64
    38  latest_dry                 0 non-null      object
    39  latest_wl_date             2 non-null      datetime64[ns]
    40  latest_ec                  2 non-null      int64
    41  latest_tds                 2 non-null      int64
    42  latest_sal_date            2 non-null      datetime64[ns]
    43  latest_ph                  2 non-null      float64
    44  latest_ph_date             2 non-null      datetime64[ns]
    45  latest_yield               0 non-null      object
    46  latest_yield_date          0 non-null      object
    47  latest_yield_extract_meth  0 non-null      object
    48  latest_yield_duration      0 non-null      object
    49  latest_yield_meth          0 non-null      object
    50  latest_ground_elev         2 non-null      float64
    51  latest_ref_elev            2 non-null      float64
    52  latest_elev_date           2 non-null      datetime64[ns]
    53  state_asset                2 non-null      object
    54  state_asset_status         2 non-null      object
    55  state_asset_retained       2 non-null      object
    56  state_asset_comments       0 non-null      object
    57  owner_code                 2 non-null      object
    58  engineering_dh             2 non-null      object
    59  water_well                 2 non-null      object
    60  water_point                2 non-null      object
    61  water_point_type           0 non-null      object
    62  mineral_dh                 2 non-null      object
    63  petroleum_well             2 non-null      object
    64  seismic_dh                 2 non-null      object
    65  stratigraphic_dh           2 non-null      object
    66  survey_horiz_accuracy      2 non-null      float64
    67  survey_horiz_meth          2 non-null      object
    68  hundred                    2 non-null      object
    69  map_sheet_no               2 non-null      int64
    70  sequence_no                2 non-null      int64
    dtypes: datetime64[ns](8), float64(16), int64(8), object(39)
    memory usage: 1.2+ KB
    >>> wells.head()
    well_id   dh_no unit_hyphen  obs_no  ... survey_horiz_meth    hundred  map_sheet_no  sequence_no
    0  CAR011  105113   7021-1058  CAR011  ...             GPSAU   CAROLINE          7021         1058
    1  KON033  253252  7022-10652  KON033  ...             GPSAU  KONGORONG          7022        10652

    [2 rows x 71 columns]

More information is in the following pages.

Aquarius
--------------------

The Aquarius products, which store continuous logger data, are a little more complex.
There is a database, to which we don't have direct access. Then there is the Aquarius Time Series (AQTS)
application, which provides access to the "raw" logger data. It comes with an Application Programming
Interface (API), which ``dew_gwdata`` uses to provide access to the data via Python.

There is also the Aquarius Web Portal (AQWP; branded as 'Water Data SA'), which is the public-facing
website. It also has an API, which can be used via Python as well.

And there is also the SWIMS Metadata database, which you can get access to via the ``dew_gwdata.webapp``
application API. This provides overview/metadata which are in turn derived from the AQTS API, but
are easier to use. They are updated each night rather than the two APIs mentioned above which are 'live'.

Water Data Entry (WDE) database
-----------------------------------

The WDE tablet application is used for routine groundwater monitoring data entry. Most of the data
entered from it goes straight into SA Geodata, but there a couple things that don't. They can be
obtained via the ``dew_gwdata.webapp`` application API.

WILMA - former Water Licensing database
--------------------------------------------

Prior to 2024 the primary Water Licensing database was called WILMA. This database has a reporting
function which Water Science staff could access called "WILMA Reporting". We regularly exported
and saved statewide usage and allocation data from WILMA into a shared drive location, and there
are functions, and an interim unofficial database, managed by the ``dew_gwdata`` package, to facilitate
access to WILMA data.

Beginning in the first quarter of 2024, a new application called mywater came into operation. As of
March 2025, there is no reporting data available from mywater. When it does become available, ``dew_gwdata``
will be modified to provide access to mywater data as well.

Gtslogs - geophysical logging data archive
---------------------------------------------------

Geophysical logs collected by DEW are indexed and stored in SA Geodata, but they are synchronised into
SA Geodata from a file archive stored on the network. ``dew_gwdata`` has functions that are able to
trawl through that archive in efficient ways.

``dew_gwdata.webapp`` "New Waterkennect" internal web application
------------------------------------------------------------------

This package also contains a web application, which utilises the functions in ``dew_gwdata``
to provide a similar level of access in a more user-friendly way, for those people who don't use
Python much. It has an API to facilitate data access via the webapp, but this could (in theory) be used from
other systems including R etc.