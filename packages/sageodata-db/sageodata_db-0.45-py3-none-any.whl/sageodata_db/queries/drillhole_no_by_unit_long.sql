SELECT dh.drillhole_no AS dh_no,                                     --col
       dh.unit_no      AS unit_long,                                 --col
       To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen,
       (Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000'))) AS obs_no --col
FROM   dhdb.dd_drillhole_vw dh
WHERE  dh.unit_no IN {UNIT_LONG} --arg UNIT_LONG (sequence of int): unit numbers in nine-character integer format e.g. 653201234
AND deletion_ind = 'N'