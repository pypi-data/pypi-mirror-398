SELECT d.strat_unit_no,                             --col Unique identifier for stratigraphic units (integer)
       u.map_symbol,                                --col Short alphanumeric code to identify strat unit.
       u.strat_name,                                --col Name of stratigraphic unit (short text)
       'DESC'                    AS note_type,      --col "DESC" indicates this record is a description of the stratigraphic unit; "COMMENT" indicates it is a metadata note (e.g. a revision of the map symbol).
       d.strat_unit_desc_type_code
       || ' '
       || d.strat_unit_desc_name AS desc_type,      --col For records where note_type = "DESC", this is either "HYDROSTRAT" or something like "STATEWIDE" / "MAP100K Tieyon". The former comes from a column in ST_STRAT_UNIT_VW. The latter come from the "ST_STRAT_UNIT_DESC" table and are formal descriptions from geological mapsheet notes.
       d.strat_unit_desc         AS note,           --col The content of the description or comment.
       d.created_by,                                --col 
       d.creation_date,                             --col 
       d.modified_by,                               --col 
       d.modified_date                              --col 
FROM   dhdb.st_strat_unit_desc_vw d
       JOIN dhdb.st_strat_unit_vw u
         ON d.strat_unit_no = u.strat_unit_no
WHERE  d.strat_unit_no in {STRAT_UNIT_NO} --arg STRAT_UNIT_NO (sequence of int): stratigraphic unit numbers or a :class:`pandas.DataFrame` with a "strat_unit_no" column
UNION
SELECT u.strat_unit_no,
       u.map_symbol,
       u.strat_name,
       'COMMENT'  AS note_type,
       NULL       AS desc_type,
       u.comments AS note,
       u.created_by,
       u.creation_date,
       NULL       AS modified_by,
       NULL       AS modified_date
FROM   dhdb.st_strat_unit_vw u
WHERE  u.strat_unit_no in {STRAT_UNIT_NO}
       AND u.comments IS NOT NULL
UNION
SELECT u.strat_unit_no,
       u.map_symbol,
       u.strat_name,
       'DESC'            AS note_type,
       'HYDROSTRAT'      AS desc_type,
       u.hydrostrat_desc AS note,
       u.created_by,
       u.creation_date,
       NULL              AS modified_by,
       NULL              AS modified_date
FROM   dhdb.st_strat_unit_vw u
WHERE  u.strat_unit_no in {STRAT_UNIT_NO}
       AND u.hydrostrat_desc IS NOT NULL
UNION
SELECT u.strat_unit_no,
       u.map_symbol,
       u.strat_name,
       'COMMENT' AS note_type,
       'HISTORY' AS desc_type,
       h.changes AS note,
       h.created_by,
       h.creation_date,
       h.modified_by,
       h.modified_date
FROM   dhdb.st_strat_unit_history_vw h
       JOIN dhdb.st_strat_unit_vw u
         ON h.strat_unit_no = u.strat_unit_no
WHERE  u.strat_unit_no in {STRAT_UNIT_NO} 