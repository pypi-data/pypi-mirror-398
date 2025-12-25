Changelog
==========

Version 0.109 (23 December 2025)
--------------------------------
- Change SQLServerDb backup host to neptune from bunyip.

Version 0.108 (12 December 2025)
--------------------------------
- Fix bug with returning "swl" on cleaning logger data instead of
  using the column "dtw" per the function call.
- Replaced loguru with standard library logging

Version 0.107 (11 December 2025)
--------------------------------
- Fix bug with RSWL/SWL correction where if there was only one elevation
  record, with no survey date, the function would raise an error. Now
  it silently uses that record.

Version 0.106 (8 December 2025)
-------------------------------
- Webapp: Fix bug where gtslogs job folder missing. Also add permit number.

Version 0.105 (20 November 2025)
--------------------------------
- Modify conversion functions to convert DTW to both SWL and RSWL, replicating
  the SA Geodata method exactly.

Version 0.104 (19 November 2025)
--------------------------------
- Fix broken extraction_data.py import
- Webapp changes:
  - Show creation & modification metadata on elevation table on well construction page
  - Sort tables and views alphabetically on schema pages.

Version 0.101 (26 August 2025)
------------------------------
- Fix bug (#12) in depth_to_elev caused by pandas fix to Series.round released in v2.3.0

Version 0.27.0 (25 May 2020)
----------------------------
- Expand and refine AQTS support

Version 0.26.0 (4 May 2020)
---------------------------
- Add initial AQTS/WP support

Version 0.24.0 (24 Mar 2020)
----------------------------
- Add water_cuts and water_cuts_by_completion queries

Version 0.23.0 (23 Mar 2020)
----------------------------
- Add wells_summary predefined query

Version 0.22.0 (17 Mar 2020)
----------------------------
- Add water_levels_between_dates query

Version 0.21.0 (17 Mar 2020)
----------------------------
- Add sample_analyses_by_chem_code and sample_analyses_by_drillholes queries
- Add missing dependencies
- Fix elevation bug where all ref_elev is empty and None instead of np.nan
- Add sample_no to salinities query
- Fix odd bug from NAP T2 water levels
- Fix exception for sites without loggers

Version 0.20.0 (24 Feb 2020)
----------------------------
- Add drilled_intervals, casing_strings; fix production_zones
- Fix anomalous_ind plot_salinity on charts

Version 0.19.0 (21 Feb 2020)
----------------------------
- Add charts.plot_salinity()

Version 0.18.0 (21 Feb 2020)
----------------------------
- Add edits/additions queries

Version 0.17.7 (18 Feb 2020)
----------------------------
- Fix bug for missing "quality_code" column in fetch_wl_data()

Version 0.17.6 (6 Feb 2020)
---------------------------
- Fix bug for empty hydstra dfs

Version 0.17.4 (3 Feb 2020)
---------------------------
- Fix #13 - handle multiple elev records with no applied dates
- Fix bug thinking that applied_date NaT is a real date

Version 0.17.3 (3 Feb 2020)
---------------------------
- Fix #12 (empty ref_elevs causes TypeError)

Version 0.17.2 (31 Jan 2020)
----------------------------
- Fix #11 (Hydstra QC "undefined" was included)

Version 0.17.1 (21 Jan 2020)
----------------------------
- Add missing "latest_status_date" column to drillhole_details_by_latest_permit
  predef. query

Version 0.17.0 (21 Jan 2020)
----------------------------
- Add drillhole_details_by_latest_permits predefined query

Version 0.16.0 (21 Jan 2020)
----------------------------
- Add drillhole_notes predefined query
- Fix bug for wells without logger data in fetch_hydstra_dtw_data()
- Fix documentation issues

Version 0.15.0 (21 Jan 2020)
-----------------------------
- Add transform_dtw_to_rswl() function primarily for Hydstra DTW data
- Add functions to retrieve data from Hydstra via hydllpx-server
    - fetch_hydstra_dtw_data() - returns raw DTW data traces with quality codes
    - hydstra_quality() - returns df about quality code segments
    - resample_logger_wls() - not all that useful
- Add fetch_wl_data() function to get a simple combination of available data
  from both SA Geodata and Hydstra. Use this!

Version 0.14.3
--------------
- CRITICAL bug fix with constructing Well objects

Version 0.14.2
--------------
- Fix bug so that a predefined query running on an empty argument list will
  still execute and return a table with zero rows.

Version 0.14.1
--------------
- Add documentation for all existing predefined queries and deploy to Gitlab Pages

Version 0.12.0
---------------
- Add site_details predefined query (for drillhole coordinate details)
- Add construction_events predefined query

Version 0.11.1
----------------
- Add geophysical log site location in lat lon

Version 0.10.2
---------------
- Add db.lookups series for common values

Version 0.10.1
---------------
- Updated all notebook tutorials to ``dew_gwdata``
- Made predefined queries more consistent
- Renamed "data_source_code" to "data_source" in "water_levels" query.
- Fixed error with "logger_data_summary" query for when no wells had logger data.

Version 0.9.2
-------------
- Renamed to ``dew_gwdata``, and changed some of the API

Version 0.8.0
-------------
- Reorganise package to remove all subpackages
- Change main SA Geodata import to: `db = wsamdata.sageodata()`

Version 0.7.3
-------------
- Finally fixed relative import bug.

Version 0.7.2
-------------
- Change relative import scheme that was causing headaches for Saeed

Version 0.5.0
----------------

- Add more predefined queries:
    - drillers_logs
    - drillhole_groups
- Add dh_name to other queries
- Add completion_date to production_zones query

Version 0.4.0
----------------

- Make predefined queries monkey-patched.
- Add predefined queries for finding wells spatially:
    - drillhole_details_by_lon_lat_rect
    - drillhole_details_by_utm_rect
- Add some other predefined queries:
    - drillhole_no_by_obs_no
    - drillhole_no_by_unit_long
    - geophys_log_metadata_by_job_no
- Add ``sageodata.gtslogs`` module (many features)

Version 0.3.0
----------------

- Add predefined queries and methods for:
    - water_levels
    - salinities
    - elevation_surveys
    - production_zones
    - strat_logs
    - geophys_log_metadata
    - logger_data_summary
    - logger_data
- Add Well and Wells integrations (thanks to python-sa-gwdata)

Version 0.2.0
----------------

- Add hydrostrat method to sageodata.Connection object

Version 0.1.0
----------------

- Initial version