SELECT u.strat_unit_no,                                 --col Unique identifier for stratigraphic units (integer)
       u.map_symbol,                                    --col Symbol for strat unit
       u.gis_code,                                      --col GIS symbol/code
       u.strat_name,                                    --col Name of strat unit
       u.equiv_strat_name,                              --col Alternative name
       u.effective_from_date    AS effective_from,      --col Date on which strat unit became used
       u.effective_to_date      AS effective_to,        --col date at which strat unit no longer became used
       u.strat_unit_current_ind AS current_ind,         --col is strat unit current now?
       u.agso_stratno           AS agso_number,         --col GA number
       u.last_updated_by,                               --col 
       u.last_updated_date,                             --col 
       u.last_revision_user,                            --col 
       u.last_revision_date,                            --col 
       u.created_by,                                    --col 
       u.creation_date                                  --col 
FROM   dhdb.st_strat_unit_vw u
WHERE  u.map_symbol = {map_symbol} --arg STRAT_UNIT_NO (sequence of int): stratigraphic unit numbers or a :class:`pandas.DataFrame` with a "strat_unit_no" column