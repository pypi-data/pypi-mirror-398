select 
    su.map_symbol || hu.hydro_subunit_code as aquifer_code, 
    hu.hydro_subunit_desc,
    su.strat_unit_no,
    su.map_symbol as map_symbol,
    su.strat_name as strat_name,
    hu.hydro_subunit_code as hydro_subunit_code
from wa_hydrostrat_subunit hu
left join st_strat_unit su on hu.strat_unit_no = su.strat_unit_no
where hydro_subunit_desc like '%SU%'
order by su.map_symbol, hu.hydro_subunit_code