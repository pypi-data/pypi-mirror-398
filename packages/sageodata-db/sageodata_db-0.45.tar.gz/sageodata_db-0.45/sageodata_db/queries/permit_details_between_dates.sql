SELECT q1.permit_no as permit_no,                     --col
q1.issue_date as issue_date,                          --col
q1.purpose as purpose,                                --col
q1.holder_name as holder_name,                        --col
q1.area_desc as area_desc,                            --col
q1.wls_comments as wls_comments,                      --col
q1.existing_unit_hyphen as existing_unit_hyphen,      --col
q1.permit_holder_address as permit_holder_address,    --col
q1.multi_non_bkf as multi_non_bkf                    --col
       -- q2.title as title,                             --col
       -- q2.plan_details as "plan",                             --col
       -- q2.parcel as parcel,                           --col
       -- q2.hundred_id as hundred_id,                   --col
       -- q2.pastoral_block as pastoral_block,           --col
       -- q2.pastoral_lease as pastoral_lease,           --col
       -- q2.ref_section as ref_section                  --col
FROM   (SELECT wp.permit_no,
               wp.issue_date,
               wp.purpose,
               wp.holder_name,
               wp.area_desc,
               wp.comments                    AS wls_comments,
               wp.wilma_map_100000_no
               || '-'
               || wp.wilma_dh_seq_no          AS existing_unit_hyphen,
               To_char(wp.holder_address_1
                       || '\n'
                       || wp.holder_address_2
                       || '\n'
                       || wp.holder_suburb
                       || ' '
                       || wp.holder_state
                       || ' '
                       || wp.holder_postcode) AS permit_holder_address,
               wp.multiple_non_bkf_wells_flag AS multi_non_bkf
        FROM   dhdbview.wp_permit_wls_vw wp
        WHERE  wp.issue_date BETWEEN To_date({from_datetime}, --arg from_datetime (:class:`pandas.Timestamp`): earliest date to search for
                                     'yyyy-mm-dd HH24:MI:SS')
                                     AND
               To_date({to_datetime}, 'yyyy-mm-dd HH24:MI:SS') --arg to_datetime (:class:`pandas.Timestamp`): latest date to search for
        ORDER  BY permit_no) q1
       -- JOIN (SELECT document_no,
       --              title_prefix
       --              || ' '
       --              || title_volume
       --              || '/'
       --              || title_folio    AS title,
       --              plan_type
       --              || ' '
       --              || plan_no        AS "plan_details",
       --              parcel_type
       --              || ' '
       --              || parcel_no      AS parcel,
       --              hundred_id,
       --              pastoral_block,
       --              pastoral_lease,
       --              reference_section AS ref_section
       --       FROM   dhdb.wp_wilma_permit_property_vw) q2
       --   ON q1.permit_no = q2.document_no
ORDER  BY issue_date 
