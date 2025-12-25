SELECT wp.permit_no AS permit_no_only,
con.drillhole_no AS dh_no,
       dh.unit_no       AS unit_long,
       To_char(dh.map_100000_no)
              || '-'
              || To_char(dh.dh_seq_no) AS unit_hyphen,
       Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,
       dh.dh_name,
       summ.aq_subaq AS aquifer,
       con.completion_date,
       con.permit_ex as site_extension,
       To_char(con.permit_no)
              || To_char(con.permit_ex) AS permit_no_full,
       wp.wilma_or_wls                  AS permit_data_source,
       wp.issue_date                    AS permit_issued,
       wp.expiry_date                   AS permit_expiry,
       wp.purpose                       AS permit_purpose,
       wp.well_use                      AS permit_well_use,
       wp.holder_name                   AS permit_holder,
       wp.comments                      AS permit_comments,
       To_char(wp.holder_address_1
              || '\n'
              || wp.holder_address_2
              || '\n'
              || wp.holder_suburb
              || ' '
              || wp.holder_state
              || ' '
              || wp.holder_postcode) AS permit_holder_address,
       wp.area_desc                  AS permit_area_desc,
       wp.multiple_non_bkf_wells_flag AS multi_non_bkf,
       con.completion_no,
       con.constrn_flag as event_type,
       con.start_depth,
       con.total_dpth                 AS total_depth,
       con.current_dpth               AS current_depth,
       con.final_dpth                 AS final_depth,
       con.final_standing_water_level AS final_swl,
       con.final_well_yield           AS final_yield,
       con.plant_operator,
       dr.holder_name as driller_name,
       dr.driller_class,
       con.comments,
       con.screened,
       con.pcem                 AS pcemented,
       con.dev                  AS developed,
       con.abndn_ind            AS abandoned,
       con.bkf_ind              AS backfilled,
       con.dry_ind              AS dry,
       con.enlarged_ind         AS enlarged,
       con.flowing_ind          AS flowing,
       con.replacement_well_ind AS replacement,
       con.commenced_date,
       con.created_by      AS construction_created_by,
       con.creation_date   AS construction_creation_date,
       con.modified_by     AS construction_modified_by,
       con.modified_date   AS construction_modified_date,
       dh.amg_easting      AS easting,
       dh.amg_northing     AS northing,
       dh.amg_zone         AS zone,
       dh.neg_lat_deg_real AS latitude,
       dh.long_deg_real    AS longitude
from dc_construction con 
left join wp_permit_wls_vw wp on con.permit_no = wp.permit_no
left join dd_drillhole dh on con.drillhole_no = dh.drillhole_no
left join dd_driller dr on con.driller_no = dr.driller_no
left join dd_drillhole_summary summ on dh.drillhole_no = summ.drillhole_no
WHERE  con.permit_no IN {PERMIT_NO}