SELECT          dh.drillhole_no AS dh_no,     --col
                dh.unit_no      AS unit_long, --col
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,            --col
                dh.dh_name                                                  AS dh_name,           --col
                dh.amg_easting                                              AS easting,           --col
                dh.amg_northing                                             AS northing,          --col
                dh.amg_zone                                                 AS zone,              --col
                dh.neg_lat_deg_real                                         AS latitude,          --col
                dh.long_deg_real                                            AS longitude,         --col
                summ.aq_subaq                                               AS aquifer,           --col
                summ.latest_permit_no                                       AS latest_permit_no,  --col
                summ.latest_permit_ex                                       AS latest_permit_ext, --col
                To_char(summ.latest_permit_no)
                                || To_char(summ.latest_permit_ex) AS latest_permit,      --col
                Trunc(summ.latest_status_date)                    AS latest_status_date, --col
                status_lut.status_desc                            AS latest_status,      --col
                summ.primary_class                                AS primary_class,      --col
                summ.earliest_well_date                           AS earliest_well_date  --col
FROM            dhdb.dd_drillhole_vw dh
join            dhdb.dd_drillhole_summary_vw summ
ON              dh.drillhole_no = summ.drillhole_no
left outer join dhdb.dd_status_vw status_lut
ON              summ.latest_status_code = status_lut.status_code
WHERE           summ.latest_permit_no IN {PERMIT_NO} --arg PERMIT_NO (sequence of int): permit numbers (not including the site extension ID) or a :class:`pandas.DataFrame` with a "permit_no" column
AND             dh.deletion_ind = 'N'