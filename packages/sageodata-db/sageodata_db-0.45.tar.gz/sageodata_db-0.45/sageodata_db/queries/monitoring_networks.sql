SELECT 
       g.group_code                                     AS group_code,            --col Name of monitoring network e.g. "CENT_ADEL"
       g.group_type_code                                  AS group_type,          --col Group type code - "OMN" = current monitoring network, "OMH" = historic monitoring network, "PR" = project i.e. random gruop, "GDU" - groundwater data upload, not used any longer, "MDU" - mineral data upload, "GDC" - groundwater data checking, not used.
       g.group_desc                                       AS group_desc,          --col Description of the network
       g.comments                                         AS group_comments,      --col Comments relating to the network - most of these are anachronistic notes from decades ago and are no longer maintained.
       g.created_by                                       AS group_created_by,    --col Username that created the group
       g.creation_date                                    AS group_creation_date, --col Date group was created
       g.modified_by                                      AS group_modified_by,   --col Username that most recently modified the group details
       g.modified_date                                    AS group_modified_date  --col Date of most recent modification
FROM   dhdb.dd_group_vw g
WHERE  g.group_type_code IN ('OMN', 'OMH')
ORDER BY g.group_type_code DESC, g.group_code ASC