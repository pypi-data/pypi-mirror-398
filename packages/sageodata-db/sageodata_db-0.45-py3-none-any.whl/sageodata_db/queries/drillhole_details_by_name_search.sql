SELECT dh.drillhole_no AS dh_no,     --col
       dh.unit_no      AS unit_long, --col
       To_char(dh.map_100000_no)
              || '-'
              || To_char(dh.dh_seq_no) AS unit_hyphen, --col
       Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,    --col
       dh.dh_name                                         AS dh_name,   --col
       dh.dh_other_name,
       dh.amg_easting                                     AS easting,   --col
       dh.amg_northing                                    AS northing,  --col
       dh.amg_zone                                        AS zone,      --col
       dh.neg_lat_deg_real                                AS latitude,  --col
       dh.long_deg_real                                   AS longitude, --col
       summ.aq_subaq                                      AS aquifer,   --col
       dh.prescribed_well_area_code                       AS pwa,       --col
       dh.presc_water_res_area_code                       AS pwra       --col
FROM   dhdb.dd_drillhole_vw dh
join   dhdb.dd_drillhole_summary_vw summ
ON     dh.drillhole_no = summ.drillhole_no
WHERE  dh.dh_name like {query_fragment_uppercase} or dh.dh_other_name like {query_fragment_uppercase}--arg query_fragment (str): name fragment for search
AND dh.deletion_ind = 'N'
AND    dh.deletion_ind = 'N'