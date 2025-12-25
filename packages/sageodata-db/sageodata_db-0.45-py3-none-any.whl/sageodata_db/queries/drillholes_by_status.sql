SELECT dh.drillhole_no AS dh_no,     --col
       To_char(dh.map_100000_no)
              || '-'
              || To_char(dh.dh_seq_no) AS unit_hyphen, --col
       Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,        --col
       dh.dh_name                                         AS dh_name,       --col
       summ.aq_subaq                                      AS aquifer,       --col
       summ.latest_status_code,
       sd2.status_desc as latest_status_desc,
       summ.latest_status_date, 
       s.status_code                                      AS status_code,   --col
       sd.status_desc                                     AS status_desc,   --col
       s.status_date                                      AS status_date,   --col
       s.created_by                                       AS created_by,    --col
       s.creation_date                                    AS creation_date, --col
       s.modified_by                                      AS modified_by,   --col
       s.modified_date                                    AS modified_date,  --col
       dh.unit_no      AS unit_long, --col
       dh.amg_easting                                     AS easting,       --col
       dh.amg_northing                                    AS northing,      --col
       dh.amg_zone                                        AS zone,          --col
       dh.neg_lat_deg_real                                AS latitude,      --col
       dh.long_deg_real                                   AS longitude     --col
FROM   dd_dh_status s
left join dd_status sd on s.status_code = sd.status_code
left join dd_drillhole dh on s.drillhole_no = dh.drillhole_no
left join dd_drillhole_summary summ on s.drillhole_no = summ.drillhole_no
left join dd_status sd2 on summ.latest_status_code = sd2.status_code
WHERE  s.status_code IN {STATUS_CODE} 
AND    dh.deletion_ind = 'N'
order by dh.drillhole_no, s.status_date