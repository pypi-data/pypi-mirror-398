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
         Trunc(wl.obs_date)                                   AS obs_date,  --col
         'DTW '
                  || To_char(wl.depth_to_water)
                  || ', SWL '
                  || To_char(wl.standing_water_level)
                  || ', RSWL '
                  || To_char(wl.rswl) AS wl,            --col
         wl.created_by                AS created_by,    --col
         wl.creation_date             AS creation_date, --col
         wl.modified_by               AS modified_by,   --col
         wl.modified_date             AS modified_date, --col
         wl.comments                  AS comments       --col
FROM     dhdb.wa_water_level_vw wl
join     dhdb.dd_drillhole_vw dh
ON       wl.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
WHERE    created_by IN {CREATED_BY} --arg CREATED_BY (sequence of str): list of SA Geodata usernames
AND      creation_date IS NOT NULL
AND dh.deletion_ind = 'N'
ORDER BY wl.creation_date DESC