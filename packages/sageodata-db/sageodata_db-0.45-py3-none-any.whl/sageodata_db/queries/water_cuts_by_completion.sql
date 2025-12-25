SELECT          dh.drillhole_no AS dh_no,     --col
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,               --col
                dh.dh_name                                                  AS dh_name,              --col
                summ.aq_subaq                                               AS aquifer,              --col
                con.aq_subaq                                                AS construction_aquifer, --col
                con.completion_no                                           AS completion_no,        --col
                Trunc(con.completion_date)                                  AS completion_date,      --col
                con.constrn_flag                                            AS event_type,           --col -- this is C or S
                con.total_dpth                                              AS total_depth,          --col
                con.final_dpth                                              AS final_depth,          --col
                To_char(con.permit_no)
                                || To_char(con.permit_ex) AS permit_no,      --col
                wc.water_cut_meas_no                      AS wcut_no,        --col
                wc.water_cut_date                         AS obs_date,       --col
                wc.water_cut_depth_from                   AS depth_from,     --col
                wc.water_cut_depth_to                     AS depth_to,       --col
                wc.depth_at_test                          AS depth_at_test,  --col
                wc.casing_at_test                         AS casing_at_test, --col
                wc.comments                               AS comments,       --col
                wc.artesian_ind                           AS artesian,       --col
                wl.depth_to_water                         AS dtw,            --col
                wl.standing_water_level                   AS swl,            --col
                wl.rswl                                   AS rswl,           --col
                wl.comments                               AS wl_comments,    --col
                s.ec                                      AS ec,             --col
                s.tds                                     AS tds,            --col
                s.comments                                AS tds_comments,   --col
                wy.well_yield                             AS yield,          --col
                wy.obs_date                               AS yield_date,     --col
                wy.comments                               AS yield_comments, --col
                wc.created_by                             AS created_by,     --col
                wc.creation_date                          AS creation_date,  --col
                wc.modified_by                            AS modified_by,    --col
                wc.modified_date                          AS modified_date,  --col
                dh.unit_no      AS unit_long, --col
                dh.amg_easting                                              AS easting,              --col
                dh.amg_northing                                             AS northing,             --col
                dh.amg_zone                                                 AS zone,                 --col
                dh.neg_lat_deg_real                                         AS latitude,             --col
                dh.long_deg_real                                            AS longitude             --col
FROM            dhdb.wa_water_cut_vw wc
left outer join dhdb.wa_water_level_vw wl
ON              wc.water_level_meas_no = wl.water_level_meas_no
left outer join dhdb.sm_sample_vw s
ON              wc.salinity_sample_no = s.sample_no
left outer join dhdb.wa_well_yield_vw wy
ON              wc.well_yield_meas_no = wy.well_yield_meas_no
left outer join dhdb.dc_construction_vw con
ON              wc.completion_no = con.completion_no
join            dhdb.dd_drillhole_vw dh
ON              con.drillhole_no = dh.drillhole_no
join            dhdb.dd_drillhole_summary_vw summ
ON              dh.drillhole_no = summ.drillhole_no
WHERE           con.completion_no IN {COMPLETION_NO} --arg COMPLETION_NO (sequence of ints): completion numbers (primary key field from construction table)
AND dh.deletion_ind = 'N'
ORDER BY        dh_no,
                completion_date,
                obs_date,
                depth_from