SELECT dh.drillhole_no AS dh_no, --col
       To_char(dh.map_100000_no)
              || '-'
              || To_char(dh.dh_seq_no) AS unit_hyphen, --col
       Trim(To_char(dh.obs_well_plan_code))
              || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,  --col
       dh.dh_name                                         AS dh_name, --col
       summ.aq_subaq                                      AS aquifer, --col
       f.file_no,                  --col
       f.file_name,                --col
       f.file_type_code, --col
       f.comments, --col
       f.file_doc_type_code, --col
       f.file_date, --col
       f.gl_auto_sync_flag, --col
       f.created_by, --col
       f.creation_date, --col
       f.modified_by, --col
       f.modified_date --col
FROM   fi_file f
join   fi_file_link fi ON     f.file_no = fi.file_no
join   dd_drillhole dh ON     fi.drillhole_no = dh.drillhole_no
join   dd_drillhole_summary summ ON     dh.drillhole_no = summ.drillhole_no
WHERE  dh.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND    dh.deletion_ind = 'N'