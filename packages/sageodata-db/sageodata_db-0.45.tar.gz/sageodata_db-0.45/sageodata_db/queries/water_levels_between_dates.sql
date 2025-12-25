SELECT   dh.drillhole_no AS dh_no,     --col
         To_char(dh.map_100000_no)
                  || '-'
                  || To_char(dh.dh_seq_no) AS unit_hyphen, --col
         Trim(To_char(dh.obs_well_plan_code))
                  || Trim(To_char(dh.obs_well_seq_no, '000')) AS obs_no,          --col
         dh.dh_name                                           AS dh_name,         --col
         summ.aq_subaq                                        AS aquifer,         --col
         wl.obs_date                                          AS obs_date,        --col
         wl.standing_water_level                              AS swl,             --col
         wl.depth_to_water                                    AS dtw,             --col
         wl.rswl                                              AS rswl,            --col
         wl.pressure                                          AS pressure,        --col
         wl.temperature                                       AS temperature,     --col
         Coalesce(wl.dry_ind, 'N')                            AS dry_ind,         --col
         wl.artesian_ind, --col
         wl.anomalous_ind                                     AS anomalous_ind,   --col
         wl.pumping_ind                                       AS pumping_ind,     --col
         wl.measured_during                                   AS measured_during, --col
         wl.data_source_code                                  AS data_source,     --col
         wl.comments                                          AS comments,        --col
         wl.created_by                                        AS created_by,      --col
         wl.creation_date                                     AS creation_date,   --col
         wl.modified_by                                       AS modified_by,     --col
         wl.modified_date                                     AS modified_date,   --col
         dh.unit_no      AS unit_long, --col
         dh.amg_easting                                       AS easting,         --col
         dh.amg_northing                                      AS northing,        --col
         dh.amg_zone                                          AS zone,            --col
         dh.neg_lat_deg_real                                  AS latitude,        --col
         dh.long_deg_real                                     AS longitude        --col
FROM     dhdb.wa_water_level_vw wl
join     dhdb.dd_drillhole_vw dh
ON       wl.drillhole_no = dh.drillhole_no
join     dhdb.dd_drillhole_summary_vw summ
ON       wl.drillhole_no = summ.drillhole_no
WHERE    wl.drillhole_no IN {DH_NO} --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND dh.deletion_ind = 'N'
AND      wl.series_type = 'T'
AND      wl.obs_date 
    BETWEEN     to_date({from_datetime}, 'yyyy-mm-dd HH24:MI:SS') --arg from_datetime (:class:`pandas.Timestamp`): earliest water level datetime
    AND         to_date({to_datetime}, 'yyyy-mm-dd HH24:MI:SS')   --arg to_datetime (:class:`pandas.Timestamp`): latest water level datetime
ORDER BY dh_no,
         obs_date
-- Beware that this query also compares times, with the default time being 
-- 00:00:00 i.e. just after midnight, so the following code does NOT return
-- water levels collected on May 10th 2018:
--
--     >>> df = db.water_levels_between_dates(
--     ...     wells,
--     ...     pd.Timestamp("2018-03-01"),
--     ...     pd.Timestamp("2018-05-10")
--     ... )
--
-- To include May 10th, use either a time explicitly:
-- 
--     >>> df = db.water_levels_between_dates(
--     ...     wells,
--     ...     pd.Timestamp("2018-03-01"),
--     ...     pd.Timestamp("2018-05-10 23:59:59")
--     ... )
--
-- Or, better, use the following day.
-- 
--     >>> df = db.water_levels_between_dates(
--     ...     wells,
--     ...     pd.Timestamp("2018-03-01"),
--     ...     pd.Timestamp("2018-05-11")
--     ... )