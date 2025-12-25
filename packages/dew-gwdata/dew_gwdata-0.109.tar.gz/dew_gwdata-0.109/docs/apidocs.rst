dew_gwdata developer API
========================

The documentation below includes some functions from ``python-sa-gwdata`` and ``sageodata_db``.

Connecting to databases and applications 
-------------------------------------------

SA Geodata
~~~~~~~~~~

.. autofunction:: dew_gwdata.sageodata
.. autoclass:: sageodata_db.SAGeodataConnection
    :members: test_alive
.. autofunction:: sageodata_db.normalize_service_name
.. autofunction:: sageodata_db.find_appropriate_server
.. autofunction:: sageodata_db.makedsn
.. autofunction:: sageodata_db.make_connection_string

Aquarius
~~~~~~~~

Finding wells
----------------------------------------------------------

The methods below are in this section are all from the ``sageodata_db``. 
However, normally you would obtain an ``SAGeodataConnection`` object
from ``dew_gwdata``:

.. code-block:: python

    >>> import dew_gwdata as gd
    >>> db = gd.sageodata()
    >>> type(db)
    <class 'sageodata_db.connection.SAGeodataConnection'>  

And then use these methods e.g. ``db.find_wells('ule200')``.

.. automethod:: sageodata_db.SAGeodataConnection.find_wells
.. automethod:: sageodata_db.SAGeodataConnection.find_wells_from_df
.. automethod:: sageodata_db.SAGeodataConnection.lookup_unit_numbers
.. automethod:: sageodata_db.SAGeodataConnection.lookup_obs_numbers

Well identifiers
------------------------------------------------------------

These functions are provided to easily convert between the two formats of unit numbers:

.. autofunction:: dew_gwdata.unit_hyphen_to_long
.. autofunction:: dew_gwdata.unit_long_to_hyphen

The functions and classes below are all from ``python-sa-gwdata`` i.e. ``sa_gwdata``:

.. autofunction:: sa_gwdata.parse_well_ids_plaintext
.. autoclass:: sa_gwdata.Well
.. autoclass:: sa_gwdata.UnitNumber
.. autoclass:: sa_gwdata.ObsNumber

Some other useful functions from ``dew_gwdata`` are:

.. autofunction:: dew_gwdata.add_well_ids_to_query_result

Groundwater data access and processing
----------------------------------------------------------

Some methods in this section are all from the ``sageodata_db`` package's 
``SAGeodataConnection`` object. However, normally you would obtain an 
``SAGeodataConnection`` object from ``dew_gwdata``:

.. code-block:: python

    >>> import dew_gwdata as gd
    >>> db = gd.sageodata()
    >>> type(db)
    <class 'sageodata_db.connection.SAGeodataConnection'>  

.. automethod:: sageodata_db.SAGeodataConnection.query

Water level
-----------

.. autofunction:: dew_gwdata.get_combined_water_level_dataset
.. autofunction:: dew_gwdata.fetch_wl_data
.. autofunction:: dew_gwdata.transform_dtw_to_rswl

Well statuses
-----------------

.. automethod:: sageodata_db.SAGeodataConnection.drillhole_status
.. autofunction:: dew_gwdata.apply_latest_status

Elevation
---------

.. automethod:: sageodata_db.SAGeodataConnection.elevation_surveys
.. autofunction:: dew_gwdata.get_dem_elev
.. autofunction:: dew_gwdata.depth_to_elev

Aquarius data access
----------------------------------------------------------

.. autofunction:: dew_gwdata.register_aq_password
.. autofunction:: dew_gwdata.get_password
.. autofunction:: dew_gwdata.convert_aq_timestamp
.. autofunction:: dew_gwdata.convert_timestamps
.. autofunction:: dew_gwdata.convert_GetLocationData_to_series
.. autofunction:: dew_gwdata.convert_GetTimeseriesMetadata_to_series
.. autofunction:: dew_gwdata.identify_aq_locations
.. autofunction:: dew_gwdata.apply_time_periods
.. autofunction:: dew_gwdata.convert_timeseries_relationships_to_graphs
.. autofunction:: dew_gwdata.draw_timeseries_relationship_graph
.. autofunction:: dew_gwdata.unstack_aq_tags
.. autofunction:: dew_gwdata.get_swims_metadata_connection

.. autoclass:: dew_gwdata.Endpoint
    :members:
.. autoclass:: dew_gwdata.DEWAquariusServer
    :members:
.. autoclass:: dew_gwdata.DEWAquarius
    :members:

.. Hydstra access
.. --------------

.. .. autofunction:: dew_gwdata.fetch_hydstra_dtw_data
.. .. autofunction:: dew_gwdata.hydstra_quality
.. .. autofunction:: dew_gwdata.resample_logger_wls

Geophysical logging data archive ("gtslogs")
----------------------------------------------------------

Newer functions:

.. autofunction:: dew_gwdata.las_to_log_type
.. autofunction:: dew_gwdata.get_las_metadata
.. autofunction:: sageodata_db.SAGeodataConnection.list_geophys_log_db_files
.. autofunction:: dew_gwdata::las_curves_to_curve_records
.. autofunction:: dew_gwdata::list_geophys_job_files
.. autofunction:: dew_gwdata::get_scan_metadata
.. autofunction:: dew_gwdata::find_parent_job_folder
.. autofunction:: dew_gwdata::find_job_folder
.. autofunction:: dew_gwdata::iter_job_folders

These are outdated methods of accessing data:

.. autoclass:: dew_gwdata.GtslogsArchiveFolder
    :members:
.. autoclass:: dew_gwdata.GLJobs
    :members:
.. autoclass:: dew_gwdata.GLJob
    :members:
.. autoclass:: dew_gwdata.LogDataFile
    :members:
.. autoclass:: dew_gwdata.CSVLogDataFile
    :members:
.. autoclass:: dew_gwdata.LASLogDataFile
    :members:

WILMA reporting
-----------------

.. autofunction:: dew_gwdata.parse_wilma_csv_export
.. autofunction:: dew_gwdata.read_allocation_csv
.. autofunction:: dew_gwdata.read_usage_csv
.. autofunction:: dew_gwdata.sourcedesc_to_unit_hyphen
.. autofunction:: dew_gwdata.read_timestamped_allocation_csv
.. autofunction:: dew_gwdata.read_timestamped_usage_csv
.. autofunction:: dew_gwdata.read_wilma_licence_parcel_shapefile
.. autofunction:: dew_gwdata.read_timestamped_wilma_licence_parcel_shapefile
.. autofunction:: dew_gwdata.iter_wilma_downloads
.. autofunction:: dew_gwdata.read_all_wilma_data
.. autofunction:: dew_gwdata.read_all_wilma_data_to_flat
.. autofunction:: dew_gwdata.filter_to_keep_latest_download
.. autofunction:: dew_gwdata.identify_dtypes
.. autofunction:: dew_gwdata.update_db
.. autofunction:: dew_gwdata.connect_to_wilma_sqlite_db
.. autofunction:: dew_gwdata.read_from_wilma_sqlite_db
.. autofunction:: dew_gwdata.query_alloc_for_licence_no
.. autofunction:: dew_gwdata.query_usage_for_unit_hyphen
.. autofunction:: dew_gwdata.query_usage_for_licence_no
.. autofunction:: dew_gwdata.total_taking
.. autofunction:: dew_gwdata.summarise_usage_table
.. autofunction:: dew_gwdata.summarise_taking_alloc_history
.. autofunction:: dew_gwdata.plot_alloc_usage_for_licenced_well
.. autofunction:: dew_gwdata.plot_alloc_usage_for_licence
.. autofunction:: dew_gwdata.plot_usage_for_licenced_well

Stratigraphy and hydrostratigraphy
---------------------------------------------------

.. autoclass:: dew_gwdata.StratigraphyHierarchy
    :members:
.. autoclass:: dew_gwdata.Hydrostratigraphy
    :members:

Well construction
--------------------------------------

.. autoclass:: dew_gwdata.ProductionZoneData
    :members:

.. autofunction:: dew_gwdata.add_construction_activity_column

Time-series manipulation
------------------------------------

.. autofunction:: dew_gwdata.linear_trend
.. autofunction:: dew_gwdata.group_into_contiguous_months
.. autofunction:: dew_gwdata.timestamp_acst

Utilities
---------------

.. autoclass:: dew_gwdata.SQLServerDb
    :members: query, run_query_for_drillholes
.. autofunction:: dew_gwdata.resize_image
.. autofunction:: dew_gwdata.camel_to_underscore
.. autofunction:: dew_gwdata.rmdir
.. autofunction:: dew_gwdata.get_pretty_file_size
.. autofunction:: dew_gwdata.cleanup_columns
.. autofunction:: dew_gwdata.chunk
.. autoclass:: dew_gwdata.SQL