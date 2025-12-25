SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,                  --col
         dh.dh_name                                           AS dh_name,                 --col
         summ.aq_subaq                                        AS aquifer,                 --col
         s.site_no                                            AS site_no,                 --col
         s.supplied_coord_type                                AS supplied_coord_type,     --col
         s.supplied_lat_degrees                               AS supplied_lat_deg,        --col
         s.supplied_lat_minutes                               AS supplied_lat_min,        --col
         s.supplied_lat_seconds                               AS supplied_lat_sec,        --col
         s.supplied_long_degrees                              AS supplied_lon_deg,        --col
         s.supplied_long_minutes                              AS supplied_lon_min,        --col
         s.supplied_long_seconds                              AS supplied_lon_sec,        --col
         s.supplied_lat_deg_real                              AS supplied_lat_dec,        --col
         s.supplied_long_deg_real                             AS supplied_lon_dec,        --col
         s.supplied_easting                                   AS supplied_easting,        --col
         s.supplied_northing                                  AS supplied_northing,       --col
         s.supplied_zone                                      AS supplied_zone,           --col
         s.supplied_datum                                     AS supplied_datum,          --col
         s.supplied_datum_verified                            AS supplied_datum_verified, --col
         s.spatial_check_code                                 AS spatial_check_code,      --col
         s.originator                                         AS originator,              --col
         s.originator_date                                    AS originator_date,         --col
         s.comments                                           AS comments,                --col
         s.digitised_by                                       AS digitised_by,            --col
         s.digitised_date                                     AS digitised_date,          --col
         s.source_map_scale                                   AS source_map_scale,        --col
         s.source_map_title                                   AS source_map_title,        --col
         s.source_map_type                                    AS source_map_type,         --col
         s.source_centre                                      AS source_centre,           --col
         s.svy_method_horiz_code                              AS horiz_survey_meth,       --col
         s.svy_accrcy_horiz                                   AS horiz_survey_accuracy,   --col
         s.air_photo_svy                                      AS air_photo_survey,        --col
         s.air_photo_no                                       AS air_photo_no,            --col
         s.air_photo_loc                                      AS air_photo_loc,           --col
         s.air_photo_set                                      AS air_photo_set,           --col
         s.created_by                                         AS created_by,              --col
         s.creation_date                                      AS creation_date,           --col
         s.modified_by                                        AS modified_by,             --col
         s.modified_date                                      AS modified_date,           --col
         s.wcr_load_no                                        AS wcr_load_no,             --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,                 --col
         dh.amg_northing                                      AS northing,                --col
         dh.amg_zone                                          AS zone,                    --col
         dh.neg_lat_deg_real                                  AS latitude,                --col
         dh.long_deg_real                                     AS longitude                --col
FROM     dhdb.site_vw s
join     dhdb.dd_drillhole_vw dh
ON       s.site_no = dh.site_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    dh.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY dh.drillhole_no,
         s.originator_date