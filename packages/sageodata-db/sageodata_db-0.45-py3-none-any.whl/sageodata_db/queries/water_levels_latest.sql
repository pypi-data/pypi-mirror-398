select wl.dh_no,
       To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,          --col
         dh.dh_name                                           AS dh_name,         --col
         summ.aq_subaq                                        AS aquifer,         --col
       wl.obs_date,
       wl.obs_year,
       wl.dtw,
       wl.swl,
       wl.rswl,
       wl.pressure,
       wl.pressure_unit,
       wl.sip,
       wl.sit,
       wl.temperature,
       wl.dry_ind,
       wl.artesian_ind,
       wl.pumping_ind,
       wl.measured_during,
       wl.anomalous_ind,
       wl.data_source,
       wl.comments,
       wl.created_by,
       wl.creation_date,
       wl.modified_by,
       wl.modified_date,
       wl.water_level_meas_no,
       dh.unit_no unit_long,
       dh.amg_easting easting,
       dh.amg_northing northing,
       dh.amg_zone zone,
       dh.neg_lat_deg_real latitude,
       dh.long_deg_real longitude
from (select drillhole_no dh_no, 
             obs_date, 
             To_number(To_char(obs_date, 'YYYY')) obs_year,
             depth_to_water dtw,
             standing_water_level swl,
             rswl,
             pressure,
             pressure_unit_code pressure_unit,
             shut_in_pressure sip,
             shut_in_time sit,
             temperature,
             dry_ind,
             artesian_ind,
             pumping_ind,
             measured_during,
             anomalous_ind,
             data_source_code data_source,
             comments,
             created_by,
             creation_date,
             modified_by,
             modified_date,
             water_level_meas_no,
             rank() over (partition by drillhole_no order by obs_date desc) rnk
      from wa_water_level
      where drillhole_no in {DH_NO}
      and series_type = 'T'
      and anomalous_ind = 'N'
      and depth_to_water is not null) wl
join dd_drillhole dh on dh_no = dh.drillhole_no
join dd_drillhole_summary summ on dh_no = summ.drillhole_no
where rnk = 1