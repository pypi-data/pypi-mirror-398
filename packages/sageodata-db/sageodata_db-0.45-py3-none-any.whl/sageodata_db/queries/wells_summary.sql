SELECT dh.drillhole_no AS dh_no,     --col
       To_char(dh.map_100000_no)
              || '-'
              || To_char(dh.dh_seq_no) AS unit_hyphen, --col
       Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,             --col
       dh.dh_name                                         AS dh_name,            --col
       dh.unit_no      AS unit_long, --col
       dh.amg_easting                                     AS easting,            --col
       dh.amg_northing                                    AS northing,           --col
       dh.amg_zone                                        AS zone,               --col
       dh.neg_lat_deg_real                                AS latitude,           --col
       dh.long_deg_real                                   AS longitude,          --col
       summ.aq_subaq                                      AS aquifer,            --col
       summ.class_all,                                                           --col
       dh.prescribed_well_area_code                       AS pwa,                --col
       dh.presc_water_res_area_code                       AS pwra,               --col
       dh.nrm_region_code                                 AS nrm,                --col
       dh.landscapesa_region_code                         AS landscape,          --col
       dh.dh_other_name                                   AS dh_other_name,      --col
       dh.parent_drillhole_no                             AS parent_dh_no,       --col
       dh.replacement_drillhole_no                        AS child_dh_no,        --col
       dh.replacement_date                                AS replaced_date,      --col
       summ.latest_status_code                            AS latest_status,      --col
       summ.latest_status_date                            AS latest_status_date, --col
       summ.purpose_code1
              || ' '
              || summ.purpose_code2
              || ' '
              || summ.purpose_code3 AS purpose,                --col
       dh.owner_code                AS owner,                  --col
       dh.orig_drilled_depth        AS orig_drilled_depth,     --col
       dh.orig_drilled_date         AS orig_drilled_date,      --col
       dh.max_drilled_depth         AS max_drilled_depth,      --col
       dh.max_drilled_depth_date    AS max_drilled_depth_date, --col
       dh.latest_open_depth         AS latest_open_depth,      --col
       dh.latest_open_depth_date    AS latest_open_depth_date, --col
       summ.latest_case_fr          AS latest_cased_from,      --col
       summ.latest_case_to          AS latest_cased_to,        --col
       summ.latest_min_diam         AS latest_casing_min_diam, --col
       summ.drill_meth1
              || ' '
              || summ.drill_meth2
              || ' '
              || summ.drill_meth3   AS drill_method,              --col
       dh.comments                  AS comments,                  --col
       summ.latest_dtw              AS latest_dtw,                --col
       summ.latest_swl              AS latest_swl,                --col
       summ.latest_rswl             AS latest_rswl,               --col
       summ.latest_dry_ind          AS latest_dry,                --col
       summ.latest_swl_date         AS latest_wl_date,            --col
       summ.latest_ec               AS latest_ec,                 --col
       summ.latest_tds              AS latest_tds,                --col
       summ.latest_sal_date         AS latest_sal_date,           --col
       summ.latest_ph               AS latest_ph,                 --col
       summ.latest_ph_date          AS latest_ph_date,            --col
       summ.latest_yield            AS latest_yield,              --col
       summ.latest_yield            AS latest_yield_date,         --col
       summ.yield_extr_code         AS latest_yield_extract_meth, --col
       summ.yield_extr_dur_hour     AS latest_yield_duration,     --col
       summ.yield_meas_method_code  AS latest_yield_meth,         --col
       summ.latest_ground_elevation AS latest_ground_elev,        --col
       summ.latest_ref_elevation    AS latest_ref_elev,           --col
       summ.latest_elevation_date   AS latest_elev_date,          --col
       dh.state_asset               AS state_asset,               --col
       dh.state_asset_status,                                     --col
       dh.state_asset_retained,                                   --col
       dh.state_asset_comments,                                   --col
       dh.owner_code,                                             --col
       dh.engineering_class         AS engineering_dh,            --col
       dh.water_well_class          AS water_well,                --col
       dh.water_point_class         AS water_point,               --col
       dh.water_point_type_code     AS water_point_type,          --col
       dh.mineral_class             AS mineral_dh,                --col
       dh.petroleum_class           AS petroleum_well,            --col
       dh.seismic_point_class       AS seismic_dh,                --col
       dh.stratigraphic_class       AS stratigraphic_dh,          --col
       dh.svy_accrcy_horiz          AS survey_horiz_accuracy,     --col
       dh.svy_method_horiz_code     AS survey_horiz_meth,         --col
       dh.hundred_name              AS hundred,                    --col
       summ.db_drillers_log,
       summ.db_litho_log as db_lith_log,
       summ.db_strat_log,
       summ.db_hydro_strat_log as db_hydrostrat_log,
       summ.db_geophysical_log,
       summ.db_pumping_test,
       summ.db_dh_doc_image,
       summ.db_dh_image as db_photo,
       summ.db_water_sample,
       summ.db_water_chem,
       summ.db_water_info,
       dh.map_100000_no AS map_sheet_no,
       dh.dh_seq_no AS sequence_no
FROM   dhdb.dd_drillhole_vw dh
join   dhdb.dd_drillhole_summary_vw summ
ON     dh.drillhole_no = summ.drillhole_no
WHERE  dh.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND    dh.deletion_ind = 'N'