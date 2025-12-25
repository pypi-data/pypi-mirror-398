SELECT   dh.drillhole_no AS dh_no, --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,               --col
         summ.aq_subaq                                        AS aquifer,              --col
         con.aq_subaq                                         AS construction_aquifer, --col
         con.completion_date                                  AS completion_date,      --col
         con.constrn_flag                                     AS event_type,           --col this is C or S
         c.seal                                               AS seal,                 --col
         c.seal_depth                                         AS seal_depth,           --col
         c.case_mtrl                                          AS seal_material,        --col
         c.case_diam                                          AS seal_diam,            --col
         c.comments                                           AS comments,             --col
         con.completion_no                                    AS completion_no,        --col
         c.created_by                                         AS created_by,           --col
         c.creation_date                                      AS creation_date,        --col
         c.modified_by                                        AS modified_by,          --col
         c.modified_date                                      AS modified_date,        --col
         dh.dh_name                                           AS dh_name,              --col
         dh.unit_no                                           AS unit_long,            --col
         dh.amg_easting                                       AS easting,              --col
         dh.amg_northing                                      AS northing,             --col
         dh.amg_zone                                          AS zone,                 --col
         dh.neg_lat_deg_real                                  AS latitude,             --col
         dh.long_deg_real                                     AS longitude             --col
FROM     dhdb.dc_casing_vw c
join     dhdb.dc_construction_vw con
ON       con.completion_no = c.completion_no
join     dhdb.dd_drillhole_vw dh
ON       con.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    con.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND      dh.deletion_ind = 'N'
AND      c.seal = 'Y'
ORDER BY dh_no,
         completion_date,
         seal_depth