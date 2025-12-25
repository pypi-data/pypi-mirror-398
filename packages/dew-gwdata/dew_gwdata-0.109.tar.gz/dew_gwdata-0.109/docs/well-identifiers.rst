Well identifiers
================

Locating wells by identifiers
------------------------------

There is a versatile utility method (:meth:`sageodata_db.SAGeodataConnection.find_wells`) 
which allows you to search for wells using their obswell number or unit numbers:

.. code-block:: python

    >>> import dew_gwdata as gd
    >>> db = gd.sageodata()
    >>> wells = db.find_wells("SLE69... YAT115, PTA 41, and 6627-6983")
    >>> wells
        well_id   dh_no unit_hyphen  ...        hundred map_sheet_no  sequence_no
    0     PTA041   27380    6528-252  ...  PORT ADELAIDE         6528          252
    1  6627-6983   45403   6627-6983  ...       NANGKITA         6627         6983
    2     YAT115   60200  6628-13231  ...         YATALA         6628        13231
    3     SLE069  198753   6028-2320  ...       SLEAFORD         6028         2320

    [4 rows x 71 columns]

The table which is returned has the all-important "dh_no" column containing drillhole numbers.
Drillhole numbers are the primary key identifier for drillholes/wells in SA Geodata, and are
used in the majority of other functions and queries in ``dew_gwdata`` for obtaining data.

There are other ways to identify wells too. What if you have a list of unit numbers? You can
use :meth:`sageodata_db.SAGeodataConnection.lookup_unit_numbers`:

.. code-block:: python

    >>> unit_nos = ["6629-1855", "672802412", 672801829]
    >>> result = db.lookup_unit_numbers(unit_nos)
    >>> result
        well_id  dh_no  unit_long unit_hyphen  ... db_dh_file earliest_well_date primary_class  class_all
    0  6629-1855  63211  662901855   6629-1855  ...          N         1974-05-30            WW         WW
    0  6728-1829  74723  672801829   6728-1829  ...          N         1955-09-20            WW         WW
    1     MOR321  75306  672802412   6728-2412  ...          N         1983-03-17            WW         WW

    [3 rows x 308 columns]

What if you have a list of obs numbers?  You can use :meth:`sageodata_db.SAGeodataConnection.lookup_obs_numbers`:

.. code-block:: python

    >>> obs_nos = ["ULE205", "SLE 81", "SLE80", "LNC015"]
    >>> result2 = db.lookup_obs_numbers(obs_nos)
    >>> result2
    well_id   dh_no  unit_long unit_hyphen  ... db_dh_file earliest_well_date primary_class  class_all
    0  ULE205  198752  602802319   6028-2319  ...          Y         2003-12-12            WW         WW
    0  SLE080  355498  602803224   6028-3224  ...          Y         2021-06-19            WW         WW
    1  SLE081  357147  602803225   6028-3225  ...          Y         2021-06-25            WW         WW
    0  LNC015   11985  602801746   6028-1746  ...          Y         1990-10-02            WW         WW

    [4 rows x 308 columns]

What if you have a spreadsheet which has well identifiers in a column, perhaps of mixed type?

.. figure:: figures/find_wells_from_df.png

You can use :meth:`sageodata_db.SAGeodataConnection.find_wells_from_df`:

.. code-block:: python

    >>> import pandas as pd
    >>> df = pd.read_excel("figures/find_wells_from_df.xlsx")
    >>> df
            Well           Status             Comment
    0     FLN 59    Visit Tuesday  This is an example
    1   5928-439     Still unsure                 NaN
    2  6028-3233              NaN          No comment
    3     ULE200              NaN                 NaN
    4     ULE183  Visit Wednesday                1234
    5     ULE183              NaN      Duplicate row.
    >>> result3 = db.find_wells_from_df(df, copy=True, return_id_cols=["dh_no", "unit_hyphen"])
    >>> result3
                parsed_id   dh_no unit_hyphen       Well           Status             Comment
    0      (obs_no, FLN059)  247522   6028-2708     FLN 59    Visit Tuesday  This is an example
    1   (unit_no, 5928-439)  247806    5928-439   5928-439     Still unsure                 NaN
    2  (unit_no, 6028-3233)  359482   6028-3233  6028-3233              NaN          No comment
    3      (obs_no, ULE200)   11177    6028-938     ULE200              NaN                 NaN
    4      (obs_no, ULE183)   11849   6028-1610     ULE183  Visit Wednesday                1234
    5      (obs_no, ULE183)   11849   6028-1610     ULE183              NaN      Duplicate row.

Searching the database by well name
-------------------------------------

This could do with some improvement! But you can pull off a search with SQL. For example to 
search for wells with "JOHNSON" in their name:

.. code-block:: python

    >>> dh_nos = db.query("select drillhole_no as dh_no from dd_drillhole where dh_name like '%JOHNSON%'")
    >>> wells = db.wells_summary(dh_nos)
    >>> wells[["dh_no", "unit_hyphen", "dh_name", "obs_no", "comments"]]
        dh_no unit_hyphen                          dh_name  obs_no                                           comments
    0     6923      5841-7                JOHNSON NO.2 BORE    None                                               None
    1    10102      5941-8        ONE TREE  (JOHNSONS NO.1)  WRA008                                               None
    2    16728     6138-19                    JOHNSONS BORE  BKN009                                               None
    3    16862      6241-6              JOHNSON'S NO 3 BORE    None                                               None
    4    77910     6733-20                     JOHNSON BORE    None                                               None
    5   208143      6241-7               NEW JOHNSON'S NO.3    None                                  Property of Peake
    6   252629     6138-89                     JOHNSONS NEW  BKN013                       Billakalina Pastoral Company
    7   161843  6628-18019                       JOHNSONS 1    None                                               None
    8   161844  6628-18020                       JOHNSONS 3    None                                               None
    9   281019    6733-183                    JOHNSONS BORE    None                        Property: Koonamore Station
    10  306169     6241-28        JOHNSONS DIRECTIONAL HOLE    None  Directional well drilled in an attempt to deco...
    11  101996    6927-184  JOHNSON (BSN-184/57) PARRAKIE 1    None                                               None

Manipulating identifiers 
-------------------------

There is a another package called python-sa-gwdata (``sa_gwdata`` in Python) which provides a few functions
and classes for manipulating well identifiers without accessing the database. These are imported into 
``dew_gwdata`` for you to use.

Common tasks might include converting between the two common formats of unit numbers:

.. code-block:: python

    >>> gd.unit_hyphen_to_long("6241-28")
    624100028
    >>> gd.unit_long_to_hyphen("624100006")
    '6241-6'

Or accessing the separate components of unit numbers (1:100K map sheet number, and sequence number):

.. code-block:: python

    >>> unit = gd.UnitNumber(624100006)
    >>> unit.map
    6241
    >>> unit.seq
    6

And similar for obs number components (observation plan code - usually the hundred - and sequence number):

.. code-block:: python

    >>> obs = gd.ObsNumber("LNC 15")
    >>> obs.plan
    'LNC'
    >>> obs.seq
    15

See all the information here:

* :class:`dew_gwdata.unit_hyphen_to_long`
* :class:`dew_gwdata.unit_long_to_hyphen`
* :class:`sa_gwdata.UnitNumber`
* :class:`sa_gwdata.ObsNumber`

Parsing identifiers
-------------------------

Another function which might be useful is the one used internally by 
:meth:`sageodata_db.SAGeodataConnection.find_wells` (shown above), which is
:func:`sa_gwdata.parse_well_ids_plaintext`. This takes some ASCII text and 
identifies *possible* well identifiers within it. 

.. code-block:: python

    >>> gd.parse_well_ids('sle15')
    [('obs_no', 'SLE015')]
    >>> gd.parse_well_ids('6628150')
    []
    >>> gd.parse_well_ids('6628-150')
    [('unit_no', '6628-150')]
    >>> gd.parse_well_ids('662800150')
    [('unit_no', '6628-150')]
    >>> gd.parse_well_ids('259001', types=["dh_no"])
    [('dh_no', '259001')]
    >>> parse_well_ids("SLE 15, SLE16, and also maybe 5910-1")
    [('unit_no', '5910-1'), ('obs_no', 'SLE015'), ('obs_no', 'SLE016'), ('obs_no', 'YBE591')]

Note that it doesn't check with the database though, hence "possible" - see "YBE591" in the 
above example, which is not a real obs number. It's better to rely on 
:meth:`sageodata_db.SAGeodataConnection.find_wells`.
