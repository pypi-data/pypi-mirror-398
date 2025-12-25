SELECT dh_no                   AS dh_no,                   --col
       
       unit_hyphen             AS unit_hyphen,             --col
       obs_no                  AS obs_no,                  --col
       dh_name                 AS dh_name,                 --col
       aquifer                 AS aquifer,                 --col
       logger_no               AS logger_no,               --col
       logger_make             AS logger_make,             --col
       logger_details          AS logger_details,          --col
       logger_type             AS logger_type,             --col
       data_type               AS data_type,               --col
       data_source_code        AS data_source_code,        --col
       test_start_date_time    AS test_start_timestamp,    --col
       pt_confidential         AS pt_confidential,         --col
       comments                AS comments,                --col
       logging_start_date_time AS start_timestamp,         --col
       logging_end_date_time   AS end_timestamp,           --col
       source_data_change_time AS source_data_change_time, --col
       dl_data_type_code       AS dl_data_type_code,       --col
       data_correction         AS data_correction,         --col
       data_correction_method  AS data_correction_method,  --col
       created_by              AS created_by,              --col
       creation_date           AS creation_date,           --col
       modified_by             AS modified_by,             --col
       modified_date           AS modified_date,            --col
       unit_long               AS unit_long,               --col
       easting                 AS easting,                 --col
       northing                AS northing,                --col
       zone                    AS zone,                    --col
       latitude                AS latitude,                --col
       longitude               AS longitude               --col
       
FROM   (
                       SELECT          dh.drillhole_no AS dh_no,
                                       dh.unit_no      AS unit_long,
                                       To_char(dh.map_100000_no)
                                                       || '-'
                                                       || To_char(dh.dh_seq_no) AS unit_hyphen,
                                       Trim(To_char(dh.obs_well_plan_code))
                                                       || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,
                                       dh.dh_name,
                                       dh.amg_easting      AS easting,
                                       dh.amg_northing     AS northing,
                                       dh.amg_zone         AS zone,
                                       dh.neg_lat_deg_real AS latitude,
                                       dh.long_deg_real    AS longitude,
                                       summ.aq_subaq       AS aquifer,
                                       l.logger_no,
                                       l.logger_make,
                                       l.logger_details,
                                       l.data_logger_type_code AS logger_type,
                                       l.data_source_code,
                                       l.test_start_date_time,
                                       l.pt_confidential_flag AS pt_confidential,
                                       l.comments ,
                                       ls.logging_end_date_time,
                                       ls.logging_start_date_time,
                                       ls.source_data_change_time ,
                                       lc.data_logger_data_type_code AS dl_data_type_code,
                                       lc.data_correction,
                                       lc.data_correction_method ,
                                       l.created_by,
                                       l.creation_date,
                                       l.modified_by,
                                       l.modified_date ,
                                       ls.db_dtw_data_logger       AS dtw,
                                       ls.db_yield_data_logger     AS yield,
                                       ls.db_ec_data_logger        AS ec,
                                       ls.db_cec_data_logger       AS cec,
                                       ls.db_temp_data_logger      AS temp,
                                       ls.db_rain_data_logger      AS rain,
                                       ls.db_hour_rain_data_logger AS hourly_rain
                       FROM            dhdb.dh_logger_vw l
                       join            dhdb.dh_logger_summary_vw ls
                       ON              l.logger_no = ls.logger_no
                       left outer join dhdb.dh_logger_correction_vw lc
                       ON              ls.logger_no = lc.logger_no
                       left outer join dhdb.dd_drillhole_vw dh
                       ON              l.drillhole_no = dh.drillhole_no
                       left outer join dhdb.dd_drillhole_summary_vw summ
                       ON              l.drillhole_no = summ.drillhole_no
                       WHERE           l.drillhole_no                                                 IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
                       AND dh.deletion_ind = 'N'
                       ORDER BY        ls.logging_start_date_time ) unpivot ( db_logger FOR data_type IN (dtw,
                                                                                                          yield,
                                                                                                          ec,
                                                                                                          cec,
                                                                                                          temp,
                                                                                                          rain,
                                                                                                          hourly_rain))
WHERE  db_logger = 'Y'