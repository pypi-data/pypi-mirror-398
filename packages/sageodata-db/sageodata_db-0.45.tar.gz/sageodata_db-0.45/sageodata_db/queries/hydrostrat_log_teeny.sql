select  lines.dh_no, 
        listagg(lines.interval_line, '\n') within group (order by lines.depth_from, lines.depth_to) as "log",
        lines.unit_hyphen,
        lines.obs_no,
        lines.dh_name,
        lines.aquifer,
        lines.easting,
        lines.northing,
        lines.unit_long,
        lines.latitude,
        lines.longitude
from (
    select log_int.dh_no, 
           log_int.depth_from,
           log_int.depth_to,
           log_int.depth_from || ' ' || unit_code as interval_line,
           log_int.unit_hyphen,
           log_int.obs_no,
           log_int.dh_name,
           log_int.aquifer,
           log_int.unit_long,
           log_int.easting,
           log_int.northing,
           log_int.latitude,
           log_int.longitude
    from (
        SELECT          dh.drillhole_no AS dh_no,
                        hs_int.hydro_depth_from                                     AS depth_from,             --col
                        hs_int.hydro_depth_to                                       AS depth_to,               --col
                        Trim(To_char(s_unit.map_symbol))                            AS unit_code,
                        To_char(dh.map_100000_no)
                                        || '-'
                                        || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                        Trim(To_char(dh.obs_well_plan_code))
                                        || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no, --col
                        dh.dh_name                                                  AS dh_name,
                        summ.aq_subaq                                               AS aquifer,
                        dh.unit_no      AS unit_long, --col
                        dh.amg_easting                                              AS easting,                     --col
                        dh.amg_northing                                             AS northing,                    --col
                        dh.neg_lat_deg_real                                         AS latitude,                    --col
                        dh.long_deg_real                                            AS longitude 
        FROM            wa_hydrostrat_int hs_int
        left outer join st_strat_unit s_unit                ON              hs_int.strat_unit_no = s_unit.strat_unit_no
        left outer join wa_hydrostrat_subint hs_subint      ON              hs_int.hydro_int_no = hs_subint.hydro_int_no
        left outer join wa_hydrostrat_subunit hs_subunit    ON              hs_subint.strat_unit_no = hs_subunit.strat_unit_no
                                                                AND             hs_subint.hydro_subunit_code = hs_subunit.hydro_subunit_code
        left outer join dd_drillhole dh                     ON              hs_int.drillhole_no = dh.drillhole_no
        left outer join dd_drillhole_summary summ           ON              hs_int.drillhole_no = summ.drillhole_no
        WHERE   hs_int.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
                AND hs_subint.hydro_subunit_code IS NULL
                AND dh.deletion_ind = 'N'
        UNION ALL
        SELECT          dh.drillhole_no AS dh_no,
                        hs_subint.hydro_depth_from                                  AS depth_from,
                        hs_subint.hydro_depth_to                                    AS depth_to,
                        to_char(s_unit.map_symbol)
                                        || '('
                                        || to_char(hs_subint.hydro_subunit_code)
                                        || ')' AS unit_code,
                        To_char(dh.map_100000_no)
                                        || '-'
                                        || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                        Trim(To_char(dh.obs_well_plan_code))
                                        || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no, --col
                        dh.dh_name                                                  AS dh_name,
                        summ.aq_subaq                                               AS aquifer,
                        dh.unit_no      AS unit_long, --col
                        dh.amg_easting                                              AS easting,                     --col
                        dh.amg_northing                                             AS northing,                    --col
                        dh.neg_lat_deg_real                                         AS latitude,                    --col
                        dh.long_deg_real                                            AS longitude 
        FROM            wa_hydrostrat_int hs_int
        left outer join st_strat_unit s_unit                ON              hs_int.strat_unit_no = s_unit.strat_unit_no
        left outer join wa_hydrostrat_subint hs_subint      ON              hs_int.hydro_int_no = hs_subint.hydro_int_no
        left outer join dd_drillhole dh                     ON              hs_int.drillhole_no = dh.drillhole_no
        left outer join dd_drillhole_summary summ           ON              hs_int.drillhole_no = summ.drillhole_no
        WHERE   hs_int.drillhole_no IN {DH_NO}
                and hs_subint.hydro_subunit_code IS NOT NULL
                AND dh.deletion_ind = 'N' 
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