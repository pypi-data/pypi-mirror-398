SELECT          dh.drillhole_no AS dh_no,     --col
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,     --col
                dh.dh_name                                                  AS dh_name,    --col
                summ.aq_subaq                                               AS aquifer,    --col
                di.driller_depth_from                                       AS depth_from, --col
                di.driller_depth_to                                         AS depth_to,   --col
                di.litho_driller_code                                       AS lith_code,  --col
                dl.litho_drillers_name                                      AS lith_name,  --col
                di.litho_desc                                               AS lith_desc,  --col
                di.litho_driller_conf                                       AS lith_conf,  --col
                di.log_no                                                   AS log_no,      --col
                l.completion_no,
                dh.unit_no      AS unit_long, --col
                dh.amg_easting                                              AS easting,    --col
                dh.amg_northing                                             AS northing,   --col
                dh.amg_zone                                                 AS zone,       --col
                dh.neg_lat_deg_real                                         AS latitude,   --col
                dh.long_deg_real                                            AS longitude  --col
from st_driller_interval di
left join st_drillers_lithology dl on di.litho_driller_code = dl.litho_drillers_code
left join st_geological_logging l on di.log_no = l.log_no
left join dd_drillhole dh on l.drillhole_no = dh.drillhole_no
left join dd_drillhole_summary summ on dh.drillhole_no = summ.drillhole_no
WHERE           di.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY        dh.drillhole_no,
                di.driller_depth_from,
                di.driller_depth_to