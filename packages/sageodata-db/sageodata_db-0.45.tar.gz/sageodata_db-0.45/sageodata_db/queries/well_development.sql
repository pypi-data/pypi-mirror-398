SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,          --col
         dh.dh_name                                           AS dh_name,         --col
         summ.aq_subaq                                        AS aquifer,         --col
         o.completion_date,
        o.dev_meth as method,
        o.dev_duration as duration,
o.comments,
                 o.created_by, o.creation_date, o.modified_by, o.modified_date,
                 o.other_constrn_detail_no,
                 c.completion_no,
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,         --col
         dh.amg_northing                                      AS northing,        --col
         dh.amg_zone                                          AS zone,            --col
         dh.neg_lat_deg_real                                  AS latitude,        --col
         dh.long_deg_real                                     AS longitude        --col
FROM dc_other_constrn_details o
join dc_construction c on o.completion_no = c.completion_no
join dd_drillhole dh on c.drillhole_no = dh.drillhole_no
join dd_drillhole_summary summ on dh.drillhole_no = summ.drillhole_no
WHERE    o.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
and o.constrn_type_code = 'WDV'
AND dh.deletion_ind = 'N'
ORDER BY dh_no