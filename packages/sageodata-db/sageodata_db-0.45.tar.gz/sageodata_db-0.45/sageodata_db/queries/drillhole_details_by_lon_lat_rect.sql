SELECT dh.drillhole_no                             AS dh_no,--col
       dh.unit_no                                  AS unit_long,--col
       To_char(dh.map_100000_no)
       || '-'
       || To_char(dh.dh_seq_no)                    AS unit_hyphen,--col
       Trim(To_char(dh.obs_well_plan_code))
       || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,--col
       dh.dh_name                                  AS dh_name,--col
       dh.amg_easting                              AS easting,--col
       dh.amg_northing                             AS northing,--col
       dh.amg_zone                                 AS zone,--col
       dh.neg_lat_deg_real                         AS latitude,--col
       dh.long_deg_real                            AS longitude,--col
       summ.aq_subaq                               AS aquifer --col
FROM   dhdb.dd_drillhole_vw dh
       JOIN dhdb.dd_drillhole_summary_vw summ
         ON dh.drillhole_no = summ.drillhole_no
WHERE  dh.long_deg_real >= {min_lon} --arg min_lon (float): minimum longitude (western boundary)
       AND dh.long_deg_real <= {max_lon} --arg max_lon (float): maximum longitude (eastern boundary)
       AND dh.neg_lat_deg_real >= {min_lat} --arg min_lat (float): minimum latitude (southern boundary)
       AND dh.neg_lat_deg_real <= {max_lat} --arg max_lat (float): maximum latitude (northern boundary)
AND dh.deletion_ind = 'N'