SELECT          dh.drillhole_no AS dh_no,                                      --col
                To_char(dh.map_100000_no)
                                || '-'
                                || To_char(dh.dh_seq_no) AS unit_hyphen,       --col
                Trim(To_char(dh.obs_well_plan_code))
                                || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,              --col
                dh.dh_name                                                  AS dh_name,             --col
                summ.aq_subaq                                               AS current_aquifer,     --col
                aqmon.constrn_date                                          AS aquifer_mon_from,    --col
                su.map_symbol
                                ||
                CASE
                                WHEN hsu.hydro_subunit_code IS NOT NULL THEN hsu.hydro_subunit_code
                                ELSE ''
                END                           AS aquifer_mon,       --col
                su.strat_name                 AS strat_name,        --col
                hsu.hydro_subunit_desc        AS aquifer_desc,      --col
                aqmon.comments                AS comments,          --col
                aqmon.created_by              AS created_by,        --col
                aqmon.creation_date           AS creation_date,     --col
                aqmon.modified_by             AS modified_by,       --col
                aqmon.modified_date           AS modified_date,     --col
                dh.unit_no                    AS unit_long,         --col
                dh.amg_easting                AS easting,           --col
                dh.amg_northing               AS northing,          --col
                dh.amg_zone                   AS zone,              --col
                dh.neg_lat_deg_real           AS latitude,          --col
                dh.long_deg_real              AS longitude          --col
FROM        dd_dh_aquifer_mon aqmon
left join   dd_drillhole dh             ON  aqmon.drillhole_no = dh.drillhole_no
left join   dd_drillhole_summary summ   ON  aqmon.drillhole_no = summ.drillhole_no
left join   st_strat_unit su            ON  aqmon.strat_unit_no = su.strat_unit_no
left join (
    SELECT DISTINCT strat_unit_no,
                    hydro_subunit_code,
                    hydro_subunit_desc
    FROM            wa_hydrostrat_subunit ) hsu
                                        ON  aqmon.strat_unit_no = hsu.strat_unit_no and aqmon.hydro_subunit_code = hsu.hydro_subunit_code
WHERE           aqmon.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND             dh.deletion_ind = 'N'
ORDER BY        dh_no,
                aquifer_mon_from