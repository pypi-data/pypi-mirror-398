SELECT     dh.drillhole_no AS dh_no,     --col 
           To_char(dh.map_100000_no)
                      || '-'
                      || To_char(dh.dh_seq_no) AS unit_hyphen, --col
           Trim(To_char(dh.obs_well_plan_code))
                      || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,      --col
           dh.dh_name                                             AS dh_name,     --col
           summ.aq_subaq                                          AS aquifer,     --col
           li.litho_depth_from                                    AS depth_from,  --col
           li.litho_depth_to                                      AS depth_to,    --col
           li.litho_approved_code1                                AS major_lith,  --col
           li.litho_approved_code2                                AS minor_lith,  --col
           li.litho_desc                                          AS description, --col
           li.log_no                                              AS log_no,       --col
           dh.unit_no      AS unit_long, --col
           dh.amg_easting                                         AS easting,     --col
           dh.amg_northing                                        AS northing,    --col
           dh.amg_zone                                            AS zone,        --col
           dh.neg_lat_deg_real                                    AS latitude,    --col
           dh.long_deg_real                                       AS longitude   --col
FROM       dhdb.dd_drillhole_vw dh
inner join dhdb.st_litho_interval_vw li
ON         dh.drillhole_no = li.drillhole_no
inner join dhdb.dd_drillhole_summary_vw summ
ON         summ.drillhole_no = dh.drillhole_no
WHERE      dh.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY   dh.drillhole_no,
           li.litho_depth_from,
           li.litho_depth_to