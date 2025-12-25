select  spr.drillhole_no as dh_no,  --col
        To_char(dh.map_100000_no) || '-' || To_char(dh.dh_seq_no) AS unit_hyphen, --col
        dh.dh_name, --col
        spr.spring_id || spr.spring_id_extension as spring_id, --col
        c.condition_date, --col
        c.mound_width as width, --col
        c.mound_relative_height as height, --col
        c.mound_length as length, --col
        c.sulphate_present_ind as sulphate, --col
        c.stromatolites_present_ind as stromatolites, --col
        c.data_source_code as data_source, --col
        c.notes as condition_notes, --col
        c.excavation_area, --col
        exp.excavation_proportion_desc as excavation_proportion, --col
        ext.excavation_type_desc as excavation_type, --col
        spr.morphological_type_code as general_morphology,  --col
        c.dominant_surfce_composition_cd as surface_composition, --col
        c.surface_expression_code as surface_expression, --col
        surf_morph.surface_morphology_desc as surface_morphology,  --col
        c.grazing_code as grazing, --col
        pdc.damage_proportion_desc as pig_damage, --col
        sdc.damage_proportion_desc as stock_damage,  --col
        c.pugging_code as pugging, --col
        observers.observers, --col
        c.created_by, --col
        c.creation_date, --col
        c.modified_by, --col
        c.modified_date, --col
        sgroup.group_desc as spring_group, --col
        complex.complex_desc as spring_complex, --col
        complex.supergroup_code as spring_supergroup, --col
        dh.unit_no      AS unit_long, --col
        dh.amg_easting                                              AS easting,              --col
        dh.amg_northing                                             AS northing,             --col
        dh.amg_zone                                                 AS zone,                 --col
        dh.neg_lat_deg_real                                         AS latitude,             --col
        dh.long_deg_real                                            AS longitude             --col
from sv_spring_condition c
left join sv_spring spr on c.spring_no = spr.spring_no
left join dd_drillhole dh on spr.drillhole_no = dh.drillhole_no
left join sv_excavation_proportion exp on c.excavation_proportion_code = exp.excavation_proportion_code
left join sv_excavation_type ext on c.excavation_type_code = ext.excavation_type_code
left join sv_damage_proportion pdc on c.pig_damage_code = pdc.damage_proportion_code
left join sv_damage_proportion sdc on c.stock_damage_code = sdc.damage_proportion_code
left join sv_surface_morphology surf_morph on c.surface_morphology_code = surf_morph.surface_morphology_code
left join (
    select sco.spring_condition_no,
           listagg(o.observer_name, ', ') within group (order by sco.creation_date) as observers
    from sv_spring_condition_observr sco
    left join sv_observer o on sco.observer_no = o.observer_no
    group by sco.spring_condition_no
    ) observers on observers.spring_condition_no = c.spring_condition_no
left join sv_group sgroup on spr.spring_id_group_code = sgroup.group_code
left join sv_complex complex on sgroup.complex_code = complex.complex_code