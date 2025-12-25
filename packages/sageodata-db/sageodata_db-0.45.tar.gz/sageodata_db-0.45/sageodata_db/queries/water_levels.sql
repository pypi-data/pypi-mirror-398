SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,          --col
         dh.dh_name                                           AS dh_name,         --col
         summ.aq_subaq                                        AS aquifer,         --col
         wl.obs_date                                          AS obs_date,        --col
         wl.standing_water_level                              AS swl,             --col
         wl.depth_to_water                                    AS dtw,             --col
         wl.rswl                                              AS rswl,            --col
         wl.pressure                                          AS pressure,        --col
         wl.pressure_unit_code AS pressure_unit, --col
         wl.shut_in_pressure AS sip, --col
         wl.shut_in_time AS sit, --col
         wl.temperature                                       AS temperature,     --col
         Coalesce(wl.dry_ind, 'N')                            AS dry_ind,         --col
         wl.artesian_ind, --col 
         wl.anomalous_ind                                     AS anomalous_ind,   --col
         wl.pumping_ind                                       AS pumping_ind,     --col
         wl.measured_during                                   AS measured_during, --col
         wl.data_source_code                                  AS datasource,      --col
         wl.comments                                          AS comments,        --col
         wl.water_level_meas_no                               AS wl_meas_no,      --col
         wl.created_by                                        AS created_by,      --col
         wl.creation_date                                     AS creation_date,   --col
         wl.modified_by                                       AS modified_by,     --col
         wl.modified_date                                     AS modified_date,   --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,         --col
         dh.amg_northing                                      AS northing,        --col
         dh.amg_zone                                          AS zone,            --col
         dh.neg_lat_deg_real                                  AS latitude,        --col
         dh.long_deg_real                                     AS longitude        --col
FROM     dhdb.wa_water_level_vw wl
join     dhdb.dd_drillhole_vw dh
ON       wl.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       wl.drillhole_no = summ.drillhole_no
WHERE    wl.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND      wl.series_type = 'T'
AND      wl.obs_date IS NOT NULL
AND dh.deletion_ind = 'N'
ORDER BY dh_no,
         obs_date