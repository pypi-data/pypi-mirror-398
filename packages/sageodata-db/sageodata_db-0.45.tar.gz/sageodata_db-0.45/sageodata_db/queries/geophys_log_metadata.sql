SELECT          dh.drillhole_no AS dh_no,     --col
                
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,        --col
                dh.dh_name                                                  AS dh_name,       --col
                summ.aq_subaq                                               AS aquifer,       --col
                hdr.job_no                                                  AS job_no,        --col
                hdr.log_hdr_no                                              AS log_hdr_no,    --col
                status_subquery.status_date                                 AS logged_date,   --col
                hdr.project_desc                                            AS project,       --col
                hdr.client_company_name                                     AS client,        --col
                site.comments                                               AS location, --col
                hdr.purpose_code                                            AS purpose,       --col
                operator_subquery.operators,                                                  --col
                hdr.vehicle_code AS vehicle,                                                  --col
                Trim(To_char(hdr.dh_name1))
                                || Trim(To_char(hdr.dh_name2)) AS gl_dh_name, --col
                Trim(To_char(hdr.permit_no))
                                || Trim(To_char(hdr.permit_ext)) AS gl_permit_no,  --col
                hdr.max_log_depth                                AS max_log_depth, --col
                hdr.comments                                     AS comments,       --col
                site.amg_easting                                            AS log_easting,   --col
                site.amg_northing                                           AS log_northing,  --col
                site.amg_zone                                               AS log_zone,      --col
                site.neg_lat_deg_real                                       AS log_latitude,  --col
                site.long_deg_real                                          AS log_longitude, --col
                dh.unit_no      AS unit_long, --col
                dh.amg_easting                                              AS easting,       --col
                dh.amg_northing                                             AS northing,      --col
                dh.amg_zone                                                 AS zone,          --col
                dh.neg_lat_deg_real                                         AS latitude,      --col
                dh.long_deg_real                                            AS longitude     --col
FROM            dhdb.gl_log_hdr_vw hdr
left outer join
                (
                         SELECT   log_hdr_no,
                                  Listagg(operator_initials, '+') within GROUP (ORDER BY operator_initials) AS operators
                         FROM     dhdb.gl_log_operator_vw
                         GROUP BY log_hdr_no ) operator_subquery
ON              hdr.log_hdr_no = operator_subquery.log_hdr_no
left outer join
                (
                       SELECT status_date,
                              log_hdr_no
                       FROM   dhdb.gl_log_status_vw
                       WHERE  status_code = 'LOGGED') status_subquery
ON              hdr.log_hdr_no = status_subquery.log_hdr_no
left outer join dhdb.site_vw site
ON              hdr.log_site_no = site.site_no
left outer join dhdb.dd_drillhole_vw dh
ON              hdr.drillhole_no = dh.drillhole_no
left outer join dhdb.dd_drillhole_summary_vw summ
ON              hdr.drillhole_no = summ.drillhole_no
WHERE           dh.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY        dh_no,
                logged_date