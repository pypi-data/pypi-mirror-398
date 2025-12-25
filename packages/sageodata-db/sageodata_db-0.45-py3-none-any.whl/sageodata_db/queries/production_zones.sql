SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,               --col
         dh.dh_name                                           AS dh_name,              --col
         summ.aq_subaq                                        AS aquifer,              --col
         con.aq_subaq                                         AS construction_aquifer, --col
         con.completion_date                                  AS completion_date,      --col
         con.constrn_flag                                     AS event_type,           --col - this is C or S
         pz.pzone_type_code                                   AS pzone_type,           --col
         pz.pzone_fr                                          AS pzone_from,           --col
         pz.pzone_fr                                          AS depth_from,           --col
         pz.pzone_to                                          AS pzone_to,             --col
         pz.pzone_to                                          AS depth_to,             --col
         pz.pzone_mtrl                                        AS pzone_material,       --col
         pz.pzone_diam                                        AS pzone_diam,           --col
         pz.aperture                                          AS aperture,             --col
         pz.outer_diam                                        AS outer_diam,           --col
         pz.trade_name                                        AS trade_name,           --col
         pz.base_completion                                   AS base_completion,      --col
         pz.comments                                          AS comments,             --col
         pz.creation_date                                     AS creation_date,        --col
         pz.created_by                                        AS created_by,           --col
         pz.modified_date                                     AS modified_date,        --col
         pz.modified_by                                       AS modified_by,          --col
         pz.pzone_no                                          AS pzone_no,             --col
         pz.wcr_load_no                                       AS wcr_load_no,          --col
         pz.wcr_load_data_no                                  AS wcr_load_data_no,      --col
         con.completion_no                                    AS completion_no,        --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,              --col
         dh.amg_northing                                      AS northing,             --col
         dh.amg_zone                                          AS zone,                 --col
         dh.neg_lat_deg_real                                  AS latitude,             --col
         dh.long_deg_real                                     AS longitude            --col
FROM     dhdb.dc_production_zone_vw pz
join     dhdb.dc_construction_vw con
ON       pz.completion_no = con.completion_no
join     dhdb.dd_drillhole_vw dh
ON       pz.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    pz.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY dh_no,
         completion_date,
         pzone_from