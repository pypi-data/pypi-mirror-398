SELECT     dh.drillhole_no AS dh_no,     --col
           To_char(dh.map_100000_no)
                      || '-'
                      || To_char(dh.dh_seq_no) AS unit_hyphen, --col
           Trim(To_char(dh.obs_well_plan_code))
                      || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,     --col
           dh.dh_name                                             AS dh_name,    --col
           summ.aq_subaq                                          AS aquifer,    --col
           su.strat_unit_no                                       ,              --col
           si.strat_depth_from                                    AS depth_from, --col
           si.strat_depth_to                                      AS depth_to,   --col
           su.strat_name                                          AS strat_name, --col
           su.gis_code                                            AS gis_code,   --col
           su.map_symbol                                          AS map_symbol, --col
           si.litho_approved_code1 
                || ' ' 
                || litho_approved_code2 AS lith_codes,              --col major and minor (if it exists) lithology codes, separated by whitespace e.g. `'SAND SILT'`
           si.strat_desc                                          AS strat_desc,  --col
           dh.unit_no      AS unit_long, --col
           dh.amg_easting                                         AS easting,    --col
           dh.amg_northing                                        AS northing,   --col
           dh.amg_zone                                            AS zone,       --col
           dh.neg_lat_deg_real                                    AS latitude,   --col
           dh.long_deg_real                                       AS longitude  --col
FROM       dhdb.dd_drillhole_vw dh
inner join dhdb.st_strat_interval_vw si
ON         dh.drillhole_no = si.drillhole_no
inner join dhdb.st_strat_unit_vw su
ON         si.strat_unit_no = su.strat_unit_no
inner join dhdb.dd_drillhole_summary_vw summ
ON         summ.drillhole_no = dh.drillhole_no
WHERE      dh.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY   dh.drillhole_no,
           si.strat_depth_from,
           si.strat_depth_to