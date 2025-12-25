select  lines.dh_no, 
        listagg(lines.interval, '\n') within group (order by lines.depth_from, lines.depth_to) as log,
        lines.unit_hyphen,
        lines.obs_no,
        lines.dh_name,
        lines.aquifer,
        lines.easting,
        lines.northing,
        lines.unit_long,
        lines.latitude,
        lines.longitude
from ( select log_int.dh_no, 
              log_int.depth_from,
              log_int.depth_to,
              Round(log_int.depth_from, 1) || ' ' || unit_code as interval,
              log_int.unit_hyphen,
              log_int.obs_no,
              log_int.dh_name,
              log_int.aquifer,
              log_int.unit_long,
              log_int.easting,
              log_int.northing,
              log_int.latitude,
              log_int.longitude
       from ( select dh.drillhole_no AS dh_no,
                     si.strat_depth_from as depth_from,
                     si.strat_depth_to as depth_to,
                     su.map_symbol as unit_code,
                     To_char(dh.map_100000_no) || '-' || To_char(dh.dh_seq_no) AS unit_hyphen,
                     Trim(To_char(dh.obs_well_plan_code)) || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,
                     dh.dh_name as dh_name,
                     summ.aq_subaq as aquifer,
                     dh.unit_no      AS unit_long, --col
                     dh.amg_easting                                              AS easting,                     --col
                     dh.amg_northing                                             AS northing,                    --col
                     dh.neg_lat_deg_real                                         AS latitude,                    --col
                     dh.long_deg_real                                            AS longitude
              from st_strat_interval si
              left join st_strat_unit su on si.strat_unit_no = su.strat_unit_no
              left join dd_drillhole dh on si.drillhole_no = dh.drillhole_no
              left join dd_drillhole_summary summ on si.drillhole_no = summ.drillhole_no
              where si.drillhole_no in {DH_NO} and dh.deletion_ind = 'N'
            ) log_int
    order by dh_no, 
             depth_from, 
             depth_to
    ) lines
group by lines.dh_no,
         lines.unit_hyphen,
         lines.obs_no,
         lines.dh_name,
         lines.aquifer,
         lines.easting,
         lines.northing,
         lines.unit_long,
         lines.latitude,
         lines.longitude