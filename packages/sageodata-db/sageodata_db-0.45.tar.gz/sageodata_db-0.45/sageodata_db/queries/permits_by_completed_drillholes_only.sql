-- This query returns information for only those drillholes which were queried.
-- So, for example, if you query a drillhole which was a replacement well,
-- then this query will not return data for the old well which was backfilled
-- under the same permit.
--
-- Use :meth:`sageodata_db.SAGeodataConnection.permits_by_completed_drillholes_all`
-- to see data for both the backfilled and replacement wells.
SELECT wp.permit_no AS permit_no_only,                          --col
con.drillhole_no               AS dh_no,                 --col
       dh.unit_no                     AS unit_long,             --col
       to_char(dh.map_100000_no)
              || '-'
              || to_char(dh.dh_seq_no) AS unit_hyphen, --col
       trim(to_char(dh.obs_well_plan_code))
              || trim(to_char(dh.obs_well_seq_no, '000')) AS obs_no,                     --col
       dh.dh_name                                         AS dh_name,                    --col
       summ.aq_subaq                                      AS aquifer,                    --col
       con.completion_date                                AS completion_date,            --col
       To_char(con.permit_no)                                   
              || To_char(con.permit_ex) AS permit_no_full,      --col
       wp.wilma_or_wls                  AS permit_data_source,  --col
       wp.issue_date                    AS permit_issued,       --col
       wp.expiry_date                   AS permit_expiry,       --col
       wp.purpose                       AS permit_purpose,      --col
       wp.well_use                      AS permit_well_use,     --col
       wp.holder_name                   AS permit_holder,       --col
       wp.comments                      AS permit_comments,     --col
       to_char(wp.holder_address_1
              || '\n'
              || wp.holder_address_2
              || '\n'
              || wp.holder_suburb
              || ' '
              || wp.holder_state
              || ' '
              || wp.holder_postcode)  AS permit_holder_address, --col
       wp.area_desc                   AS permit_area_desc,      --col
       wp.multiple_non_bkf_wells_flag AS multi_non_bkf,         --col
       
       con.completion_no                                  AS completion_no,              --col
       con.start_depth                                    AS start_depth,                --col
       con.total_dpth                                     AS total_depth,                --col
       con.current_dpth                                   AS current_depth,              --col
       con.final_dpth                                     AS final_depth,                --col
       con.final_standing_water_level                     AS final_swl,                  --col
       con.final_well_yield                               AS final_yield,                --col
       con.comments                                       AS comments,                   --col
       con.screened                                       AS screened,                   --col
       con.pcem                                           AS pcemented,                  --col
       con.dev                                            AS developed,                  --col
       con.abndn_ind                                      AS abandoned,                  --col
       con.bkf_ind                                        AS backfilled,                 --col
       con.dry_ind                                        AS dry,                        --col
       con.enlarged_ind                                   AS enlarged,                   --col
       con.flowing_ind                                    AS flowing,                    --col
       con.replacement_well_ind                           AS replacement,                --col
       con.commenced_date                                 AS commenced_date,             --col
       con.created_by                                     AS construction_created_by,    --col
       con.creation_date                                  AS construction_creation_date, --col
       con.modified_by                                    AS construction_modified_by,   --col
       con.modified_date                                  AS construction_modified_date, --col
       dh.amg_easting                                     AS easting,                    --col
       dh.amg_northing                                    AS northing,                   --col
       dh.amg_zone                                        AS zone,                       --col
       dh.neg_lat_deg_real                                AS latitude,                   --col
       dh.long_deg_real                                   AS longitude                   --col
FROM   dhdbview.wp_permit_wls_vw wp
join   dhdb.dc_construction_vw con
ON     wp.permit_no = con.permit_no
join   dhdb.dd_drillhole_vw dh
ON     con.drillhole_no = dh.drillhole_no
join   dhdb.dd_drillhole_summary_vw summ
ON     dh.drillhole_no = summ.drillhole_no
WHERE  con.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
