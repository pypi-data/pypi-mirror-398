SELECT ld.logger_no                   AS logger_no,        --col
       ld.logger_date_time            AS "timestamp",      --col
       ld.data_value                  AS data_value,       --col
       ld.corrected_value             AS corrected_value,  --col
       ld.verified_flag               AS verified,         --col
       ld.logger_test_elapsed_seconds AS test_elapsed_sec, --col
       ld.data_logger_data_type_code  AS data_type         --col
FROM   dhdb.dh_logger_data_vw ld
WHERE  ld.logger_no IN {LOGGER_NO} --arg LOGGER_NO (sequence of int): sequence of primary keys for logger datasets (see :meth:`sageodata_db.SAGeodataConnection.logger_data_summary`)