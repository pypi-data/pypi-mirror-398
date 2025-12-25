SELECT          hdr.log_hdr_no,
                hdr.job_no,
                f.file_no,
                f.file_name as filename
FROM            dhdb.fi_file f
join            dhdb.fi_file_link_vw flink
ON              f.file_no = flink.file_no
join            dhdb.gl_log_hdr_vw hdr
ON              flink.gl_log_hdr_no = hdr.log_hdr_no
WHERE           flink.file_data_type_code = 'GL'
ORDER BY        hdr.job_no