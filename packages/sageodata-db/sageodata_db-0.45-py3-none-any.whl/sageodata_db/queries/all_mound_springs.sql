select  spr.drillhole_no as dh_no,  --col
        To_char(dh.map_100000_no) || '-' || To_char(dh.dh_seq_no) AS unit_hyphen, --col
        dh.dh_name, --col
        spr.spring_no, --col
        spr.spring_id || spr.spring_id_extension as spring_id, --col
        sm.aq_subaq as aquifer, --col
        spr.spring_active_ind as active, --col
        spr.morphological_type_code as general_morphology, --col
        lform.landform_element_desc as landform_element, --col
        elform.erosion_landform_pattern_desc as erosion_landform_pattern, --col
        dh.comments as dh_comment, --col
        spr.notes as spring_notes, --col
        spr.created_by, --col
        spr.creation_date, --col
        spr.modified_by, --col
        spr.modified_date, --col
        sgroup.group_desc as spring_group, --col
        complex.complex_desc as spring_complex, --col
        complex.supergroup_code as spring_supergroup, --col
        dh.unit_no      AS unit_long, --col
        dh.amg_easting                                              AS easting,              --col
        dh.amg_northing                                             AS northing,             --col
        dh.amg_zone                                                 AS zone,                 --col
        dh.neg_lat_deg_real                                         AS latitude,             --col
        dh.long_deg_real                                            AS longitude             --col
from sv_spring spr
left join dd_drillhole dh on spr.drillhole_no = dh.drillhole_no
left join dd_drillhole_summary sm on dh.drillhole_no = sm.drillhole_no
left join sv_group sgroup on spr.spring_id_group_code = sgroup.group_code
left join sv_complex complex on sgroup.complex_code = complex.complex_code
left join sv_landform_element lform on spr.landform_element_code = lform.landform_element_code
left join sv_erosion_landform_pattern elform on spr.erosion_landform_pattern_code = elform.erosion_landform_pattern_code