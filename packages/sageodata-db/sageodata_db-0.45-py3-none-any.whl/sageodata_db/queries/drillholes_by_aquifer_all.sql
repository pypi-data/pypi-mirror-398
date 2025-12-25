select dh.drillhole_no as dh_no,
dh.unit_no      AS unit_long, --col
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,           --col
                dh.dh_name                                                  AS dh_name,          --col
sm.aq_subaq as current_aquifer,
st.map_symbol || aq.hydro_subunit_code as aquifer_code,
aq.constrn_date as aquifer_mon_from,
aq.comments as aquifer_mon_comments
from dd_dh_aquifer_mon aq
left join st_strat_unit st on aq.strat_unit_no = st.strat_unit_no
left join dd_drillhole dh on aq.drillhole_no = dh.drillhole_no
left join dd_drillhole_summary sm on dh.drillhole_no = sm.drillhole_no
where st.map_symbol || aq.hydro_subunit_code in {AQUIFER_CODE}
and dh.deletion_ind = 'N'
order by dh_no, aquifer_mon_from