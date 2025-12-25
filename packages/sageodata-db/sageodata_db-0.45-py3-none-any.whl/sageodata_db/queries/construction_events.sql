SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,               --col
         dh.dh_name                                           AS dh_name,              --col
         summ.aq_subaq                                        AS aquifer,              --col
         con.aq_subaq                                         AS construction_aquifer, --col
         con.well_completion_report_id                        AS wcr_id,               --col well completion report ID e.g. ``'WCR-3221'``, from the drillers WCR form submission
         dr.holder_name as driller_name,
         dr.driller_class as driller_class,
         con.plant_operator,            --col
         con.completion_date                                  AS completion_date,      --col
         con.constrn_flag                                     AS event_type,           --col this is C or S
         con.orig_flag,
         con.start_depth                                      AS start_depth,          --col
         con.total_dpth                                       AS total_depth,          --col
         con.current_dpth                                     AS current_depth,        --col
         con.final_dpth                                       AS final_depth,          --col
         To_char(con.permit_no)
                  || To_char(con.permit_ex) AS permit_no,            --col permit number always including site e.g. ``'232411B'``
         con.permit_no    AS permit_no_only, --col permit number excluding site ID e.g. ``'232411'``
         con.permit_ex as site_extension,
         To_char(con.permit_no)
                  || To_char(con.permit_ex) AS permit_no_full,   --col permit number including site ID e.g. ``'232411B'``
         sum.drill_meth                     AS drill_method,         --col
         sum.drill_fr                       AS drill_from,           --col
         sum.drill_to                       AS drill_to,             --col
         sum.drill_diam                     AS drill_diam,           --col
         sum.case_mtrl                      AS casing_material,      --col
         sum.case_fr                        AS casing_from,          --col
         sum.case_to                        AS casing_to,            --col
         sum.case_diam                      AS casing_diam,          --col
         sum.min_diam                       AS casing_min_diam,      --col
         sum.pzone_type                     AS pzone_type,           --col
         sum.pzone_mtrl                     AS pzone_material,       --col
         sum.pzone_fr                       AS pzone_from,           --col
         sum.pzone_to                       AS pzone_to,             --col
         sum.pzone_diam                     AS pzone_diam,           --col
         sum.pcem_fr                        AS pcement_from,         --col
         sum.pcem_to                        AS pcement_to,           --col
         sum.dev_meth                       AS development_method,   --col
         sum.dev_duration                   AS development_duration, --col
         con.final_standing_water_level     AS final_swl,            --col
         con.final_well_yield               AS final_yield,          --col
         con.comments                       AS comments,             --col
         con.screened                       AS screened,             --col
         con.pcem                           AS pcemented,            --col
         con.dev                            AS developed,            --col
         con.abndn_ind                      AS abandoned,            --col
         con.bkf_ind                        AS backfilled,           --col
         con.dry_ind                        AS dry,                  --col
         con.enlarged_ind                   AS enlarged,             --col
         con.flowing_ind                    AS flowing,              --col
         con.replacement_well_ind           AS replacement,          --col
         con.rework_rehab                   AS rehabilitated,        --col
         con.latest                         AS latest,               --col
         con.max_case                       AS max_case,             --col
         con.orig_case                      AS orig_case,            --col
         con.lod_case                       AS lod_case,             --col
         con.from_flag                      AS from_flag,            --col
         con.core_flag                      AS core_flag,            --col
         con.commenced_date                 AS commenced_date,       --col
         con.created_by                     AS created_by,           --col
         con.creation_date                  AS creation_date,        --col
         con.modified_by                    AS modified_by,          --col
         con.modified_date                  AS modified_date,        --col
         con.completion_no                                    AS completion_no,        --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,              --col
         dh.amg_northing                                      AS northing,             --col
         dh.amg_zone                                          AS zone,                 --col
         dh.neg_lat_deg_real                                  AS latitude,             --col
         dh.long_deg_real                                     AS longitude            --col
FROM     dhdb.dc_construction_vw con
join     dhdb.dc_construction_summary_vw sum
on con.completion_no = sum.completion_no
join     dhdb.dd_drillhole_vw dh
ON       con.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       dh.drillhole_no = summ.drillhole_no
left join dd_driller dr on con.driller_no = dr.driller_no
WHERE    con.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY dh_no,
         completion_date