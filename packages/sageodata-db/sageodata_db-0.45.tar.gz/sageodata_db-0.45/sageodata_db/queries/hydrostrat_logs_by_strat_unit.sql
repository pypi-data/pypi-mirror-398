-- This query is a union of both "hydrostratigraphic interval" i.e. the
-- stratigraphic unit ("map_symbol" -> "unit_code") from dhdb.wa_hydrostrat_int_vw
-- and the "hydrostratigraphic sub-interval" i.e. ("hydro_subunit_code" ->
-- "unit_code") from dhdb.wa_hydrostrat_subint_vw, in a single table.
SELECT          dh.drillhole_no AS dh_no,     --col
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no, --col
                dh.dh_name                                                  AS dh_name,
                summ.aq_subaq                                               AS aquifer,                     --col
                hs_int.hydro_depth_from                                     AS unit_depth_from,             --col
                hs_int.hydro_depth_to                                       AS unit_depth_to,               --col
                Trim(To_char(s_unit.map_symbol))                            AS unit_code,                   --col
                Trim(To_char(s_unit.strat_name))                            AS unit_desc,                   --col
                hs_int.hydro_depth_from                                     AS hyd_int_depth_from,          --col
                hs_int.hydro_depth_to                                       AS hyd_int_depth_to,            --col
                hs_int.hydro_depth_to_greater_flag                          AS hyd_int_depth_to_greater,    --col
                hs_int.comments                                             AS hyd_int_comment,             --col
                s_unit.map_symbol                                           AS hyd_int_code,                --col
                s_unit.strat_name                                           AS hyd_int_name,                --col
                s_unit.hydrostrat_desc                                      AS hyd_int_desc,                --col
                hs_subint.hydro_depth_from                                  AS hyd_subint_depth_from,       --col
                hs_subint.hydro_depth_to                                    AS hyd_subint_depth_to,         --col
                hs_subint.hydro_depth_to_greater_flag                       AS hyd_subint_depth_to_greater, --col
                hs_subint.hydro_subunit_code                                AS hyd_subint_code,             --col
                hs_subunit.hydro_subunit_desc                               AS hyd_subint_desc,             --col
                hs_subint.comments                                          AS hyd_subint_comments,          --col
                hs_int.log_no,
                dh.unit_no      AS unit_long, --col
                dh.amg_easting                                              AS easting,                     --col
                dh.amg_northing                                             AS northing,                    --col
                dh.amg_zone                                                 AS zone,                        --col
                dh.neg_lat_deg_real                                         AS latitude,                    --col
                dh.long_deg_real                                            AS longitude                   --col
FROM            dhdb.wa_hydrostrat_int_vw hs_int
left outer join dhdb.st_strat_unit_vw s_unit
ON              hs_int.strat_unit_no = s_unit.strat_unit_no
left outer join dhdb.wa_hydrostrat_subint_vw hs_subint
ON              hs_int.hydro_int_no = hs_subint.hydro_int_no
left outer join dhdb.wa_hydrostrat_subunit_vw hs_subunit
ON              hs_subint.strat_unit_no = hs_subunit.strat_unit_no
AND             hs_subint.hydro_subunit_code = hs_subunit.hydro_subunit_code
left outer join dhdb.dd_drillhole_vw dh
ON              hs_int.drillhole_no = dh.drillhole_no
left outer join dhdb.dd_drillhole_summary_vw summ
ON              hs_int.drillhole_no = summ.drillhole_no
WHERE           hs_int.strat_unit_no IN {STRAT_UNIT_NO}
AND dh.deletion_ind = 'N'