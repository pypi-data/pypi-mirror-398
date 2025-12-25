select counts_query.latest_edited_date, --col
       counts_query.latest_edited_by,   --col
       codes_query.aquifer_codes,       --col
       counts_query.count_wells,        --col
       counts_query.count_comments      --col
from (
    select  
        trunc(coalesce(aq.modified_date, aq.creation_date)) as latest_edited_date,
        coalesce(aq.modified_by, aq.created_by) as latest_edited_by,
        count(distinct aq.drillhole_no) as count_wells,
        count(distinct aq.comments) as count_comments
    from dd_dh_aquifer_mon aq
    left join st_strat_unit su on aq.strat_unit_no = su.strat_unit_no
    where coalesce(aq.modified_date, aq.creation_date) >= to_date({start_timestamp}, 'YYYY-MM-DD') --arg
      and coalesce(aq.modified_date, aq.creation_date) <= to_date({end_timestamp}, 'YYYY-MM-DD')   --arg
    group by 
        trunc(coalesce(aq.modified_date, aq.creation_date)),
        coalesce(aq.modified_by, aq.created_by)
    order by latest_edited_date desc, latest_edited_by
) counts_query
left join (
    select latest_edited_date,
           latest_edited_by,
           listagg(aquifer_code, ', ') within group (order by aquifer_code) as aquifer_codes
    from (
        select distinct 
            trunc(coalesce(aq.modified_date, aq.creation_date)) as latest_edited_date,
            coalesce(aq.modified_by, aq.created_by) as latest_edited_by,
            su.map_symbol || aq.hydro_subunit_code as aquifer_code
        from dd_dh_aquifer_mon aq
        left join st_strat_unit su on aq.strat_unit_no = su.strat_unit_no
        where coalesce(aq.modified_date, aq.creation_date) >= to_date({start_timestamp}, 'YYYY-MM-DD')
          and coalesce(aq.modified_date, aq.creation_date) <= to_date({end_timestamp}, 'YYYY-MM-DD')
    )
    group by latest_edited_date, latest_edited_by
    order by latest_edited_date desc, latest_edited_by
) codes_query
    on counts_query.latest_edited_date = codes_query.latest_edited_date
    and counts_query.latest_edited_by = codes_query.latest_edited_by