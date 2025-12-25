SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,                    --col
         dh.dh_name                                           AS dh_name,                   --col
         summ.aq_subaq                                        AS aquifer,                   --col
         con.aq_subaq                                         AS construction_aquifer,      --col
         con.completion_date                                  AS completion_date,           --col
         con.constrn_flag                                     AS event_type,                --col this is C or S
         other.constrn_type_code                              AS other_type,                --col 
         other.int_from                                       AS depth_from,                --col 
         other.int_to                                         AS depth_to,                  --col 
         other.constrn_material_code                          AS material,                  --col 
         other.diam                                           AS diameter,                  --col 
         other.aperture                                       AS aperture,                  --col 
         other.dev_meth                                       AS dev_method,                --col 
         other.dev_duration                                   AS dev_duration,              --col 
         other.gsp_placement_method                           AS gravel_placement_method,   --col 
         other.gravel_sand_size,                                                            --col 
         other.grout_cement AS grout_cement_weight,                                         --col 
         other.grout_water  AS grout_water_volume,                                          --col 
         other.grout_details,                                                               --col 
         other.retardant_details,                                                           --col 
         other.comments,                                                                    --col 
         other.created_by,                                                                  --col 
         other.creation_date,                                                               --col 
         other.modified_by,                                                                 --col 
         other.modified_date,                                                               --col 
         other.wcr_load_no,                                                                  --col 
         con.completion_no                                    AS completion_no,             --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,                   --col
         dh.amg_northing                                      AS northing,                  --col
         dh.amg_zone                                          AS zone,                      --col
         dh.neg_lat_deg_real                                  AS latitude,                  --col
         dh.long_deg_real                                     AS longitude                 --col
FROM     dhdb.dc_other_constrn_details_vw other
join     dhdb.dc_construction_vw con
ON       other.completion_no = con.completion_no
join     dhdb.dd_drillhole_vw dh
ON       con.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    con.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND      dh.deletion_ind = 'N'
ORDER BY dh_no,
         completion_date