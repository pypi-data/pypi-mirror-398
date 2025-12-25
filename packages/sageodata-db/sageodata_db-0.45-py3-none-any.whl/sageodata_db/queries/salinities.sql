SELECT   dh.drillhole_no AS dh_no,     --col
         
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,            --col
         dh.dh_name                                           AS dh_name,           --col
         summ.aq_subaq                                        AS aquifer,           --col
         s.collected_date                                     AS collected_date,    --col
         s.sample_depth_from as depth_from,
         s.sample_depth_to as depth_to,
         s.tds                                                AS tds,               --col
         s.ec                                                 AS ec,                --col
         s.ph                                                 AS ph,                --col
         s.sample_no                                          AS sample_no,         --col
         s.temperature                                        AS sample_temp,       --col
         s.sample_type                                        AS sample_type,       --col
         s.series_type                                        AS series_type,       --col
         s.anomalous_ind                                      AS anomalous_ind,     --col
         s.test_place_code                                    AS test_place,        --col
         s.extr_method_code                                   AS extract_method,    --col
         s.measured_during                                    AS measured_during,   --col
         s.collected_by                                       AS collected_by,      --col
         s.collected_by_company                               AS collected_company, --col
         s.data_source_code                                   AS data_source,       --col
         s.comments                                           AS comments,          --col
         s.email_address_sent AS email_address, --col
         s.created_by                                         AS created_by,        --col
         s.creation_date                                      AS creation_date,     --col
         s.modified_by                                        AS modified_by,       --col
         s.modified_date                                      AS modified_date,      --col
         s.field_id                                           AS field_id,          --col
         dh.amg_easting                                       AS amg_easting,       --col
         dh.amg_northing                                      AS amg_northing,      --col
         dh.amg_zone                                          AS amg_zone,          --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,           --col
         dh.amg_northing                                      AS northing,          --col
         dh.amg_zone                                          AS zone,              --col
         dh.neg_lat_deg_real                                  AS latitude,          --col
         dh.long_deg_real                                     AS longitude         --col
FROM     dhdb.sm_sample_vw s
join     dhdb.dd_drillhole_vw dh
ON       s.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       s.drillhole_no = summ.drillhole_no
WHERE    s.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND      s.series_type = 'T'
AND      s.collected_date IS NOT NULL
AND      s.sample_type != 'R'
AND dh.deletion_ind = 'N'
ORDER BY dh_no,
         s.collected_date