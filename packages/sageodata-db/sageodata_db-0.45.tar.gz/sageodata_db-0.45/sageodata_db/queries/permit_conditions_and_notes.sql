SELECT   permit_no  AS permit_no,  --col Permit number.
         "type"     AS "type",     --col Type (either "condition" or "note")
         "id"       AS "id",       --col ID
         "contents" AS "contents"  --col Contents of the condition or note.
from     (
                select wp.permit_no,
                       'condition'         AS "type",
                       cond.condition_id   AS "id",
                       cond.condition_desc AS "contents"
                FROM   dhdbview.wp_permit_wls_vw wp
                join   dhdbview.wp_permit_condition_wls_vw cond
                ON     wp.permit_no = cond.permit_no
                WHERE  wp.permit_no IN {PERMIT_NO} --arg PERMIT_NO (sequence of int): permit numbers (not including the site extension ID) or a :class:`pandas.DataFrame` with a "permit_no" column
                UNION
                SELECT wp.permit_no,
                       'note'         AS "type",
                       note.note_id   AS "id",
                       note.note_desc AS "contents"
                FROM   dhdbview.wp_permit_wls_vw wp
                join   dhdbview.wp_permit_note_wls_vw note
                ON     wp.permit_no = note.permit_no
                WHERE  wp.permit_no IN {PERMIT_NO})
ORDER BY permit_no,
         "type",
         "id"