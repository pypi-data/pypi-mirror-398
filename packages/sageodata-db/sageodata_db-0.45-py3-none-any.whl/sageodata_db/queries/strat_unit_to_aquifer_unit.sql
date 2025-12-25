select 
su.map_symbol || hu.hydro_subunit_code as aquifer_code, 
hu.hydro_subunit_desc,
queried_su.strat_unit_no,
queried_su.map_symbol as queried_map_symbol,
queried_su.strat_name as queried_strat_name,
su.strat_unit_no as aquifer_strat_unit_no,
su.map_symbol as aquifer_map_symbol, 
hu.hydro_subunit_code as aquifer_hydro_subunit_code
from wa_hydrostrat_subunit hu
left join st_strat_unit su on hu.strat_unit_no = su.strat_unit_no
left join ( select * from st_strat_unit where strat_unit_no = {strat_unit_no} ) queried_su on queried_su.strat_unit_no = {strat_unit_no}
where hydro_subunit_desc like '%SU{strat_unit_no}%'