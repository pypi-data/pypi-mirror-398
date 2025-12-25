SELECT dh.drillhole_no AS dh_no,     --col
       To_char(dh.map_100000_no)
              || '-'
              || To_char(dh.dh_seq_no) AS unit_hyphen, --col
       Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,        --col
       dh.dh_name                                         AS dh_name,       --col
       summ.aq_subaq                                      AS aquifer,       --col
       p.class_code,
       p.purpose_code, --col
       pd.purpose_desc,
       p.prioflag as purpose_priority,
       p.created_by                                       AS created_by,    --col
       p.creation_date                                    AS creation_date, --col
       p.modified_by                                      AS modified_by,   --col
       p.modified_date                                    AS modified_date,  --col
       dh.unit_no      AS unit_long, --col
       dh.amg_easting                                     AS easting,       --col
       dh.amg_northing                                    AS northing,      --col
       dh.amg_zone                                        AS zone,          --col
       dh.neg_lat_deg_real                                AS latitude,      --col
       dh.long_deg_real                                   AS longitude     --col
FROM   dd_dh_purpose p
left join dd_purpose pd on p.class_code = pd.class_code and p.purpose_code = pd.purpose_code
left join dd_drillhole dh on p.drillhole_no = dh.drillhole_no
left join dd_drillhole_summary summ on p.drillhole_no = summ.drillhole_no
WHERE  p.purpose_code IN {PURPOSE_CODE} --arg 
AND    dh.deletion_ind = 'N'
order by dh.drillhole_no, p.prioflag