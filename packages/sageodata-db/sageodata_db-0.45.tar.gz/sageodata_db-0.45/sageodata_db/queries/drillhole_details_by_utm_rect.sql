-- Use MGA94
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
WHERE  dh.amg_easting >= {min_easting} --arg min_easting (float): minimum easting (western boundary)
       AND dh.amg_easting <= {max_easting} --arg max_easting (float): maximum easting (eastern boundary)
       AND dh.amg_northing >= {min_northing} --arg min_northing (float): minimum northing (southern boundary)
       AND dh.amg_northing <= {max_northing} --arg max_northing (float): maximum northing (northern boundary)
       AND dh.amg_zone = {utm_zone} --arg utm_zone (int): MGA94 zone (do not include the letter)
AND dh.deletion_ind = 'N'