SELECT    dh.drillhole_no                        dh_no,                 --col
          Count(DISTINCT llog.log_no)            drill_or_lith_logs,    --col
          Count(DISTINCT slog.log_no)            strat_or_hydro_logs,   --col
          Count(DISTINCT wl.water_level_meas_no) water_levels,          --col
          Count(DISTINCT elev.elevation_no)      elev_surveys,          --col
          Count(DISTINCT aq_group.drillhole_no)  aquarius_flag,         --col
          Count(DISTINCT sal.sample_no)          salinities,            --col
          Count(DISTINCT wcut.water_cut_meas_no) water_cuts,            --col
          Count(DISTINCT gl.log_hdr_no)          geophys_logs,          --col
          Count(DISTINCT docimage.drillhole_no)  dh_docimg_flag,        --col
          Count(DISTINCT photo.drillhole_no)     photo_flag             --col
FROM      dhdb.dd_drillhole_vw dh
left join
          (
                 SELECT water_level_meas_no,
                        series_type,
                        drillhole_no
                 FROM   dhdb.wa_water_level_vw wl
                 WHERE  wl.drillhole_no IN {DH_NO}
                 AND    series_type = 'T') wl
ON        dh.drillhole_no = wl.drillhole_no
left join
          (
                 SELECT log_no,
                        drillhole_no
                 FROM   dhdb.st_geological_logging_vw
                 WHERE  drillhole_no       IN {DH_NO}
                 AND    geol_log_type_code IN ('L',
                                               'D')) llog
ON        dh.drillhole_no = llog.drillhole_no
left join
          (
                 SELECT log_no,
                        drillhole_no
                 FROM   dhdb.st_geological_logging_vw
                 WHERE  drillhole_no       IN {DH_NO}
                 AND    geol_log_type_code IN ('S',
                                               'H')) slog
ON        dh.drillhole_no = slog.drillhole_no
left join
          (
                 SELECT sample_no,
                        sample_type,
                        drillhole_no
                 FROM   dhdb.sm_sample_vw
                 WHERE  drillhole_no IN {DH_NO}
                 AND    sample_type in ('S', 'W')) sal
ON        dh.drillhole_no = sal.drillhole_no
left join dhdb.wa_water_cut_vw wcut
ON        dh.drillhole_no = wcut.drillhole_no
left join dhdb.gl_log_hdr_vw gl
ON        dh.drillhole_no = gl.drillhole_no
left join dhdb.dd_drillhole_doc_image_geod_vw docimage
ON        dh.drillhole_no = docimage.drillhole_no
left join dhdb.dd_drillhole_image_geod_vw photo
ON        dh.drillhole_no = photo.drillhole_no
left join dhdb.dd_elevation_vw elev
ON        dh.drillhole_no = elev.drillhole_no
left join
          (
                 SELECT drillhole_no
                 FROM   dhdb.dd_dh_group_vw
                 WHERE  drillhole_no IN {DH_NO}
                 AND    group_code = 'AQUARIUS') aq_group
ON        dh.drillhole_no = aq_group.drillhole_no
WHERE     dh.drillhole_no IN {DH_NO}        --arg DH_NO (sequence of int): drillhole numbers or a :class:`pandas.DataFrame` with a "dh_no" column
AND       dh.deletion_ind = 'N'
GROUP BY  dh.drillhole_no