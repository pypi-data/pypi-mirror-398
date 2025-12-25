SELECT   dh.drillhole_no AS dh_no,     --col
         dh.unit_no      AS unit_long, --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,    --col
         dh.dh_name                                           AS dh_name,   --col
         dh.amg_easting                                       AS easting,   --col
         dh.amg_northing                                      AS northing,  --col
         dh.amg_zone                                          AS zone,      --col
         dh.neg_lat_deg_real                                  AS latitude,  --col
         dh.long_deg_real                                     AS longitude, --col
         summ.aq_subaq                                        AS aquifer,   --col
         Trunc(elev.elev_date)                                AS obs_date,  --col
         'ground '
                  || To_char(elev.grnd_elev)
                  || ', ref '
                  || To_char(elev.ref_elev)
                  || ', applied '
                  || To_char(Trunc(elev.applied_date)) AS elev,          --col
         elev.created_by                               AS created_by,    --col
         elev.creation_date                            AS creation_date, --col
         elev.modified_by                              AS modified_by,   --col
         elev.modified_date                            AS modified_date, --col
         elev.comments                                 AS comments       --col
FROM     dhdb.dd_elevation_vw elev
join     dhdb.dd_drillhole_vw dh
ON       elev.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    modified_by IN {MODIFIED_BY}   --arg MODIFIED_BY (sequence of str): list of SA Geodata usernames
AND      modified_date IS NOT NULL
AND dh.deletion_ind = 'N'
ORDER BY elev.modified_date DESC