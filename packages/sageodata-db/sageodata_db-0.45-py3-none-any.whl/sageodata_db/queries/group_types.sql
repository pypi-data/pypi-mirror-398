SELECT         
       g.group_type_code                                  AS group_type,          
       g.group_type_desc                                       AS group_type_desc          
       
FROM   dhdb.dd_group_type_vw g
order by case when group_type_code = 'OMN' then 10
              when group_type_code = 'PR' then 20
              when group_type_code = 'MIN' then 21
              when group_type_code = 'OMH' then 30
              when group_type_code = 'ARC' then 31
              when group_type_code = 'GDC' then 40
              when group_type_code = 'GDU' then 50
              when group_type_code = 'MDU' then 60
              else 70 end, group_type_code