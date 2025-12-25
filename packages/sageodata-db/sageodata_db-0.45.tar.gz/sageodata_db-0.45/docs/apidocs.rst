#####################################################################
sageodata_db developer API
#####################################################################

Connecting to the database
==========================================================================================

.. autofunction:: sageodata_db.connect


Configuration
==========================================================================================

.. autoattribute:: sageodata_db.config.PROD_SERVER
.. autoattribute:: sageodata_db.config.TEST_SERVER

.. autofunction:: sageodata_db.normalize_service_name
.. autofunction:: sageodata_db.find_appropriate_server
.. autofunction:: sageodata_db.makedsn
.. autofunction:: sageodata_db.make_connection_string

Predefined queries
==========================================================================================

.. autofunction:: sageodata_db.get_predefined_query_filenames
.. autofunction:: sageodata_db.load_predefined_query

Parsing SQL templates
==========================================================================================

.. autoclass:: sageodata_db.SQL
    :members: