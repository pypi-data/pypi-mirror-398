select trunc(creation_date)                                  as creation_date, 
       to_char(min(creation_date), 'HH24:MI') || ' to ' ||
       to_char(max(creation_date), 'HH24:MI')                  as creation_times,
       round((max(creation_date) - min(creation_date)) * 24 * 60, 0) as creation_time_span_mins,
       created_by,
       min(trunc(collected_date)) || ' to ' || 
       max(trunc(collected_date))                            as collection_dates,
       count(distinct sample_no)                             as count_unique_samples, 
       count(distinct drillhole_no) as count_unique_wells,
       count(distinct email_address_sent) as email_addresses
from sm_sample
where sample_type = 'S' and creation_date >= to_date({start_timestamp}, 'YYYY-MM-DD') and creation_date <= to_date({end_timestamp}, 'YYYY-MM-DD')
group by trunc(creation_date), created_by
order by trunc(creation_date) desc