SELECT          dh.drillhole_no AS dh_no,     --col
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen, --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,               --col
                dh.dh_name                                                  AS dh_name,              --col
                ar.sample_no                                                AS sample_no,            --col
                s.collected_date                                            AS collected_date,       --col
                s.temperature                                               AS sample_temp,          --col
                ar.sample_type                                              AS sample_type,          --col
                s.series_type                                               AS series_type,          --col
                s.anomalous_ind                                             AS anomalous_ind,        --col
                s.test_place_code                                           AS test_place,           --col
                s.extr_method_code                                          AS extract_method,       --col
                s.measured_during                                           AS measured_during,      --col
                s.collected_by                                              AS collected_by,         --col
                s.collected_by_company                                      AS collected_company,    --col
                s.data_source_code                                          AS data_source,          --col
                ar.sample_analysis_no                                       AS sample_analysis_no,   --col
                ar.chem_code                                                AS chem_code,            --col
                ard.chem_name                                               AS chem_name,            --col
                ar.chem_value                                               AS value,                --col
                ar.chem_unit_code                                           AS unit,                 --col
                meth.mnemonic                                               AS analysis_method_code, --col
                meth.chem_method_desc                                       AS analysis_method,      --col
                meth.laboratory_code                                        AS lab,                  --col
                meth.digestion_code                                         AS digestion,            --col
                meth.determination_code                                     AS determination,        --col
                lims.ldl_ppm                                                AS lower_dl_ppm,         --col
                lims.udl_ppm                                                AS upper_dl_ppm,         --col
                lims.precision_ppm                                          AS precision_ppm,        --col
                ar.microanalysis_no                                         AS microanalysis_no,     --col
                ar.created_by                                               AS created_by,           --col
                ar.creation_date                                            AS creation_date,        --col
                ar.modified_by                                              AS modified_by,          --col
                ar.modified_date                                            AS modified_date,        --col
                dh.unit_no                                                  AS unit_long,            --col
                dh.amg_easting                                              AS easting,              --col
                dh.amg_northing                                             AS northing,             --col
                dh.amg_zone                                                 AS zone,                 --col
                dh.neg_lat_deg_real                                         AS latitude,             --col
                dh.long_deg_real                                            AS longitude,            --col
                summ.aq_subaq                                               AS aquifer               --col
FROM            dhdb.sm_analysis_result_vw ar
left outer join dhdb.sm_sample_vw s
ON              ar.sample_no = s.sample_no
left outer join dhdb.sm_chem_method_vw meth
ON              ar.chem_method_no = meth.chem_method_no
left outer join dhdb.sm_chem_vw ard
ON              ar.chem_code = ard.chem_code
left outer join dhdb.sm_chem_meth_chem_vw lims
ON              ar.chem_method_no = lims.chem_method_no
AND             ar.chem_code = lims.chem_code
left outer join dhdb.dd_drillhole_vw dh
ON              s.drillhole_no = dh.drillhole_no
inner join      dhdb.dd_drillhole_summary_vw summ
ON              dh.drillhole_no = summ.drillhole_no
WHERE           ar.chem_code IN {CHEM_CODE} --arg CHEM_CODE (sequence of str): sequence of chemical analysis codes.
AND dh.deletion_ind = 'N'