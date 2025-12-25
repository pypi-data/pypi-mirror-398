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
         con.constrn_flag                                     AS event_type,           --col this is C or S
         d.drill_meth                                         AS drill_method,         --col
         d.drill_fr                                           AS depth_from,           --col
         d.drill_to                                           AS depth_to,             --col
         d.diam                                               AS diam,                 --col
         d.core_flag                                          AS core_flag,            --col
         d.length                                             AS length,               --col
         d.width                                              AS width,                --col
         d.comments                                           AS comments,             --col
         d.created_by                                         AS created_by,           --col
         d.creation_date                                      AS creation_date,        --col
         d.modified_by                                        AS modified_by,          --col
         d.modified_date                                      AS modified_date,        --col
         con.completion_no                                    AS completion_no,        --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,              --col
         dh.amg_northing                                      AS northing,             --col
         dh.amg_zone                                          AS zone,                 --col
         dh.neg_lat_deg_real                                  AS latitude,             --col
         dh.long_deg_real                                     AS longitude             --col
FROM     dhdb.dc_drilling_vw d
join     dhdb.dc_construction_vw con
ON       d.completion_no = con.completion_no
join     dhdb.dd_drillhole_vw dh
ON       con.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    con.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY dh_no,
         completion_date,
         depth_from