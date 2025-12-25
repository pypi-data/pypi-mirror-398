select trunc(creation_date)                                  as creation_date, 
       to_char(min(creation_date), 'HH24:MI') || ' to ' ||
       to_char(max(creation_date), 'HH24:MI')                  as creation_times,
       round((max(creation_date) - min(creation_date)) * 24 * 60, 0) as creation_time_span_mins,
       created_by,
       min(trunc(obs_date)) || ' to ' || 
       max(trunc(obs_date))                            as collection_dates,
       measured_during,
       count(distinct water_level_meas_no)                             as count_unique_observations, 
       count(distinct drillhole_no) as count_unique_wells,
       count(distinct comments) as count_unique_comments
from wa_water_level
where depth_to_water is not null and creation_date >= to_date({start_timestamp}, 'YYYY-MM-DD') and creation_date <= to_date({end_timestamp}, 'YYYY-MM-DD')
group by trunc(creation_date), created_by, measured_during
order by trunc(creation_date) desc