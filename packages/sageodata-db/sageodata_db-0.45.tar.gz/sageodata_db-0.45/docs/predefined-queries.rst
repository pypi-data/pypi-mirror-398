.. _predefined-queries-label:

####################################
Predefined queries
####################################

.. py:currentmodule:: sageodata_db

.. autofunction:: connect
    :no-index:
.. autoclass:: SAGeodataConnection
    :members: test_alive, find_wells, find_wells_from_df, query, find_edits_by, find_additions_by, find_replacements, find_replacement_history, _predefined_query, _create_well_instances
    :exclude-members: SQL

.. automethod:: sageodata_db.SAGeodataConnection::all_replacement_drillholes
.. automethod:: sageodata_db.SAGeodataConnection::aquifers_monitored
.. automethod:: sageodata_db.SAGeodataConnection::casing_strings
.. automethod:: sageodata_db.SAGeodataConnection::chem_codes
.. automethod:: sageodata_db.SAGeodataConnection::construction_events
.. automethod:: sageodata_db.SAGeodataConnection::drilled_intervals
.. automethod:: sageodata_db.SAGeodataConnection::drillers_logs
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_details
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_details_all
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_details_by_latest_permit
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_details_by_lon_lat_rect
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_details_by_pwa
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_details_by_pwra
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_details_by_utm_rect
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_document_image_list
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_groups
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_image_list
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_no_by_obs_no
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_no_by_unit_long
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_notes
.. automethod:: sageodata_db.SAGeodataConnection::drillhole_status
.. automethod:: sageodata_db.SAGeodataConnection::drillholes_all
.. automethod:: sageodata_db.SAGeodataConnection::drillholes_by_aquifer_all
.. automethod:: sageodata_db.SAGeodataConnection::elevation_additions
.. automethod:: sageodata_db.SAGeodataConnection::elevation_edits
.. automethod:: sageodata_db.SAGeodataConnection::elevation_surveys
.. automethod:: sageodata_db.SAGeodataConnection::geophys_log_files_by_job_no
.. automethod:: sageodata_db.SAGeodataConnection::geophys_log_files_by_log_hdr_no
.. automethod:: sageodata_db.SAGeodataConnection::geophys_log_metadata
.. automethod:: sageodata_db.SAGeodataConnection::geophys_log_metadata_by_job_no
.. automethod:: sageodata_db.SAGeodataConnection::hydrostrat_logs
.. automethod:: sageodata_db.SAGeodataConnection::lith_logs
.. automethod:: sageodata_db.SAGeodataConnection::logger_data
.. automethod:: sageodata_db.SAGeodataConnection::logger_data_by_dh
.. automethod:: sageodata_db.SAGeodataConnection::logger_data_summary
.. automethod:: sageodata_db.SAGeodataConnection::logger_wl_data
.. automethod:: sageodata_db.SAGeodataConnection::logger_wl_data_by_dh
.. automethod:: sageodata_db.SAGeodataConnection::other_construction_items
.. automethod:: sageodata_db.SAGeodataConnection::permit_conditions_and_notes
.. automethod:: sageodata_db.SAGeodataConnection::permit_details
.. automethod:: sageodata_db.SAGeodataConnection::permit_details_between_dates
.. automethod:: sageodata_db.SAGeodataConnection::permits_by_completed_drillholes_all
.. automethod:: sageodata_db.SAGeodataConnection::permits_by_completed_drillholes_only
.. automethod:: sageodata_db.SAGeodataConnection::production_zones
.. automethod:: sageodata_db.SAGeodataConnection::salinities
.. automethod:: sageodata_db.SAGeodataConnection::salinity_additions
.. automethod:: sageodata_db.SAGeodataConnection::salinity_edits
.. automethod:: sageodata_db.SAGeodataConnection::sample_analyses_by_chem_code
.. automethod:: sageodata_db.SAGeodataConnection::sample_analyses_by_drillholes
.. automethod:: sageodata_db.SAGeodataConnection::site_details
.. automethod:: sageodata_db.SAGeodataConnection::strat_logs
.. automethod:: sageodata_db.SAGeodataConnection::water_cuts
.. automethod:: sageodata_db.SAGeodataConnection::water_cuts_by_completion
.. automethod:: sageodata_db.SAGeodataConnection::water_level_additions
.. automethod:: sageodata_db.SAGeodataConnection::water_level_edits
.. automethod:: sageodata_db.SAGeodataConnection::water_levels
.. automethod:: sageodata_db.SAGeodataConnection::water_levels_between_dates
.. automethod:: sageodata_db.SAGeodataConnection::wells_in_group_type
.. automethod:: sageodata_db.SAGeodataConnection::wells_in_groups
.. automethod:: sageodata_db.SAGeodataConnection::wells_summary

