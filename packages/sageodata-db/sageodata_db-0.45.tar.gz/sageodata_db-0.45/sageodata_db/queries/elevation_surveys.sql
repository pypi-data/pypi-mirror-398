SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,                    --col
         dh.dh_name                                           AS dh_name,                   --col
         summ.aq_subaq                                        AS aquifer,                   --col
         elev.ref_point_type                                  AS ref_point_type,            --col
         elev.ref_elev                                        AS ref_elev,                  --col
         elev.elev_date                                       AS elev_date,                 --col
         elev.grnd_elev                                       AS ground_elev,               --col
         elev.vert_accrcy                                     AS vert_accuracy,             --col
         elev.svy_meth                                        AS survey_meth,               --col
         elev.applied_date                                    AS applied_date,              --col
         elev.ref_height                                      AS ref_height,                --col
         elev.dist_elev_point_to_ground                       AS dist_elev_point_to_ground, --col
         elev.comments                                        AS comments,                  --col
         elev.created_by                                      AS created_by,                --col
         elev.creation_date                                   AS creation_date,             --col
         elev.modified_by                                     AS modified_by,               --col
         elev.modified_date                                   AS modified_date,              --col
         elev.elevation_no                                    AS elev_no,                   --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,                   --col
         dh.amg_northing                                      AS northing,                  --col
         dh.amg_zone                                          AS zone,                      --col
         dh.neg_lat_deg_real                                  AS latitude,                  --col
         dh.long_deg_real                                     AS longitude                 --col
FROM     dhdb.dd_elevation_vw elev
join     dhdb.dd_drillhole_vw dh
ON       elev.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    elev.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY dh_no ,
         elev_date