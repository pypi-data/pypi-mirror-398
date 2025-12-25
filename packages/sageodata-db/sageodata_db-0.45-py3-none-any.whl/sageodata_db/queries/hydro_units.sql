select 

su.map_symbol || '(' || hu.hydro_subunit_code || ')' as unit_code,
hu.hydro_subunit_desc as unit_desc,
'Hydrostrat log sub-interval' as used_as,
su.strat_unit_no, 
su.map_symbol,
su.strat_name,
hu.hydro_subunit_code
from wa_hydrostrat_subunit hu
join st_strat_unit su on hu.strat_unit_no = su.strat_unit_no
where hu.hydro_subunit_desc like 'HS LOG ONLY%'

union all
select 
su.map_symbol || hu.hydro_subunit_code as unit_code,
hu.hydro_subunit_desc as unit_desc,
'Aquifer monitored (via hydrostrat sub-unit)' as used_as,
su.strat_unit_no, 
su.map_symbol,
su.strat_name,
hu.hydro_subunit_code
from wa_hydrostrat_subunit hu
join st_strat_unit su on hu.strat_unit_no = su.strat_unit_no
where hu.hydro_subunit_desc like '%[SU%'

union all
select distinct 
su.map_symbol as unit_code,
su.strat_name as unit_desc,
'Hydrostrat/Strat log interval' as used_as,
su.strat_unit_no, 
su.map_symbol,
su.strat_name,
'' as hydro_subunit_code
from wa_hydrostrat_int hu
join st_strat_unit su on hu.strat_unit_no = su.strat_unit_no

union all
select distinct
su.map_symbol as unit_code,
su.strat_name as unit_desc,
'Aquifer monitored (via strat unit only)' as used_as,
su.strat_unit_no,
su.map_symbol,
su.strat_name,
null as hydro_subunit_code
from dd_dh_aquifer_mon aq
join st_strat_unit su on aq.strat_unit_no = su.strat_unit_no

order by unit_code