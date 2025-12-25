select 
dh.drillhole_no as dh_no,
c.completion_date,
c.permit_no as permit_no,
c.permit_ex as site_id,
c.permit_no || c.permit_ex as permit_no_full,
wp.purpose_desc as permit_purpose,
c.well_completion_report_id as wcr_id,
p.holder_name as permit_holder,
dr.holder_name as driller_licence_holder,
c.plant_operator,
dr.driller_licence_no as driller_licence,
dh.dh_creation_date,
dh.dh_created_by,
dh.dh_modified_date,
dh.dh_modified_by
from dc_construction c
left join dd_drillhole dh on c.drillhole_no = dh.drillhole_no
left join dd_well_constrn_permit p on p.permit_no = c.permit_no
left join dd_driller dr on c.driller_no = dr.driller_no
left join wp_purpose wp on p.purpose_id = wp.purpose_id
where dh.water_well_class = 'Y'
and dh.drillhole_no in {DH_NO}
and dh.deletion_ind = 'N'