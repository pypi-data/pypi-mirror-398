SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,          --col
         dh.dh_name                                           AS dh_name,         --col
         summ.aq_subaq                                        AS aquifer,         --col
         y.obs_date,
         y.well_yield,
         y.well_yield_depth_from as depth_from,
         y.well_yield_depth_to as depth_to,
         y.extr_method_code as extract_method,
         y.extr_method_duration as duration_hrs,
         y.intake_depth,
         y.draw_down as drawdown,
         y.water_level,
         y.measured_during,
        y.series_type,
        y.data_source_code as data_source,
        y.comments,
         y.well_yield_meas_no,
         y.created_by, y.creation_date, y.modified_by, y.modified_date,
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,         --col
         dh.amg_northing                                      AS northing,        --col
         dh.amg_zone                                          AS zone,            --col
         dh.neg_lat_deg_real                                  AS latitude,        --col
         dh.long_deg_real                                     AS longitude        --col
FROM wa_well_yield y
join dd_drillhole dh on y.drillhole_no = dh.drillhole_no
join dd_drillhole_summary summ on dh.drillhole_no = summ.drillhole_no
WHERE    y.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
ORDER BY dh_no,
         obs_date