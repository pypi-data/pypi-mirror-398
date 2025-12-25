 SELECT          dh.drillhole_no AS dh_no,
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen,
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,
                dh.dh_name,
                summ.aq_subaq          AS aquifer,
                l.geol_log_type_code AS log_type,
                l.geol_logging_date  AS log_date,
                l.geol_logger_type_code AS logged_by,
                l.geol_logger_name      AS logged_by_name,
                l.geol_logging_org_code AS logged_by_org,
                org.geol_logging_org_name AS logged_by_org_name,
                l.comments,
                l.instrument_type_code,
                l.measure_method_code,
                l.acquisition_date,
                l.created_by,
                l.creation_date,
                l.modified_by,
                l.modified_date,
                l.log_no,
                l.completion_no,
                dh.unit_no      AS unit_long,
                dh.amg_easting         AS easting,
                dh.amg_northing        AS northing,
                dh.amg_zone            AS zone,
                dh.neg_lat_deg_real    AS latitude,
                dh.long_deg_real       AS longitude
FROM            dhdb.dd_drillhole_vw dh
inner join      dhdb.st_geological_logging_vw l
ON              dh.drillhole_no = l.drillhole_no
left outer join dhdb.st_geological_logging_org_vw org
ON              l.geol_logging_org_code = org.geol_logging_org_code
inner join      dhdb.dd_drillhole_summary_vw summ
ON              summ.drillhole_no = dh.drillhole_no
WHERE           dh.drillhole_no IN {DH_NO}
ORDER BY        dh.drillhole_no,
                l.geol_logging_date