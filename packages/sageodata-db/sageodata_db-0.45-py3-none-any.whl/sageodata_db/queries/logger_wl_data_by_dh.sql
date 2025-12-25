SELECT ld.logger_no                   AS logger_no,        --col
       ld.logger_date_time            AS "timestamp",      --col
       ld.anomalous_ind               AS anomalous_ind,    --col
       ld.data_value                  AS data_value,       --col
       ld.corrected_value             AS corrected_value,  --col
       ld.data_value                  AS dtw,              --col
       ld.swl                         AS swl,              --col
       ld.rswl                        AS rswl,             --col
       ld.verified_flag               AS verified,         --col
       ld.logger_test_elapsed_seconds AS test_elapsed_sec, --col
       ld.data_logger_data_type_code  AS data_type,        --col
       ld.created_by                  AS created_by,       --col
       ld.creation_date               AS creation_date,    --col
       ld.modified_by                 AS modified_by,      --col
       ld.modified_date               AS modified_date     --col
FROM   dhdb.dh_logger_wl_data_vw ld
join dhdb.dd_drillhole_vw dh on ld.drillhole_no = dh.drillhole_no
WHERE  ld.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
