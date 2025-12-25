SELECT q1.dh_no,
       q1.unit_hyphen,
       q1.new_dh_no,
       To_char(dhr.map_100000_no)
       || '-'
       || To_char(dhr.dh_seq_no) AS new_unit_hyphen,
       q1.replaced_from
FROM   (SELECT dh.drillhole_no             AS dh_no,
               To_char(dh.map_100000_no)
               || '-'
               || To_char(dh.dh_seq_no)    AS unit_hyphen,
               dh.replacement_drillhole_no AS new_dh_no,
               dh.replacement_date         AS replaced_from
        FROM   dhdb.dd_drillhole_vw dh
        WHERE  dh.deletion_ind = 'N'
               AND dh.replacement_drillhole_no IS NOT NULL) q1
       join dhdb.dd_drillhole_vw dhr
         ON q1.new_dh_no = dhr.drillhole_no 
        WHERE q1.dh_no IN {DH_NO} or q1.new_dh_no IN {DH_NO}