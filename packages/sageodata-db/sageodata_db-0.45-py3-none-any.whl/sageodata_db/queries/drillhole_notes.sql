SELECT dh.drillhole_no AS dh_no,     --col
       To_char(dh.map_100000_no)
              || '-'
              || To_char(dh.dh_seq_no) AS unit_hyphen, --col
       Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,        --col
       dh.dh_name                                         AS dh_name,       --col
       summ.aq_subaq                                      AS aquifer,       --col
       n.dh_note_no                                       AS note_no,       --col
       n.notes_date                                       AS note_date,     --col
       n.notes_by                                         AS author,        --col
       n.notes                                            AS note,          --col
       n.created_by                                       AS created_by,    --col
       n.creation_date                                    AS creation_date, --col
       n.modified_by                                      AS modified_by,   --col
       n.modified_date                                    AS modified_date, --col
       dh.unit_no      AS unit_long, --col
       dh.amg_easting                                     AS easting,       --col
       dh.amg_northing                                    AS northing,      --col
       dh.amg_zone                                        AS zone,          --col
       dh.neg_lat_deg_real                                AS latitude,      --col
       dh.long_deg_real                                   AS longitude     --col
FROM   dhdb.dd_drillhole_vw dh
join   dhdb.dd_drillhole_summary_vw summ
ON     dh.drillhole_no = summ.drillhole_no
join   dhdb.dd_dh_note_vw n
ON     dh.drillhole_no = n.drillhole_no
WHERE  dh.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND    dh.deletion_ind = 'N'