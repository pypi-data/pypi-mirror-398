select  dh.drillhole_no AS dh_no,     --col
        To_char(dh.map_100000_no)
                || '-'
                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
        Trim(To_char(dh.obs_well_plan_code))
                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,                    --col
        dh.dh_name                                           AS dh_name,                   --col
        su.map_symbol
                                ||
                CASE
                                WHEN hsu.hydro_subunit_code IS NOT NULL THEN hsu.hydro_subunit_code
                                ELSE ''
                END                           AS aquifer, --col
        su.map_symbol as major_unit,            --col
        hsu.hydro_subunit_code as sub_unit,   --col
        aq.comments,                            --col
        aq.created_by,                          --col
        aq.creation_date,                       --col
        aq.modified_by,                         --col
        aq.modified_date                        --col
from dd_dh_aquifer_mon aq
left join st_strat_unit su on su.strat_unit_no = aq.strat_unit_no
left join wa_hydrostrat_subunit hsu on aq.strat_unit_no = hsu.strat_unit_no and aq.hydro_subunit_code = hsu.hydro_subunit_code
left join dd_drillhole dh on aq.drillhole_no = dh.drillhole_no
where substr(su.map_symbol, -1) <> upper(substr(su.map_symbol, -1))
order by aq.modified_date desc, aq.creation_date desc