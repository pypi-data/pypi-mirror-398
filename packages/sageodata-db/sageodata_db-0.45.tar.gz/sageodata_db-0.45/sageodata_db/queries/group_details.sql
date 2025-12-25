SELECT 
       g.group_code                                     AS group_code,            
       g.group_type_code                                  AS group_type,          
       g.group_desc                                       AS group_desc,          
       count(d.drillhole_no) as total_wells,
       wl.current_swl_wells,
       tds.current_tds_wells,
       g.comments                                         AS group_comments,      
       g.created_by                                       AS group_created_by,    
       g.creation_date                                    AS group_creation_date, 
       g.modified_by                                      AS group_modified_by,   
       g.modified_date                                    AS group_modified_date  
FROM   dhdb.dd_group_vw g
join dhdb.dd_dh_group_vw d on g.group_code = d.group_code
left join (select count(drillhole_no) as current_swl_wells, group_code from dhdb.dd_dh_group_vw where stand_water_level_status = 'C' group by group_code) wl on g.group_code = wl.group_code
left join (select count(drillhole_no) as current_tds_wells, group_code from dhdb.dd_dh_group_vw where salinity_status = 'C' group by group_code) tds on g.group_code = tds.group_code
group by g.group_code, g.group_type_code, g.group_desc, g.comments, g.created_by, g.creation_date, g.modified_by, g.modified_date, wl.current_swl_wells, tds.current_tds_wells
order by case when group_type_code = 'OMN' then 1
              when group_type_code = 'PR' then 2
              when group_type_code = 'OMH' then 3
              when group_type_code = 'GDC' then 4
              when group_type_code = 'GDU' then 5
              when group_type_code = 'MDU' then 6
              else 7 end, group_code