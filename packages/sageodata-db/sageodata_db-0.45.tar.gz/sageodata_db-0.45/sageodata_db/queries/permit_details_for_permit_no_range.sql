SELECT          q1.permit_no             AS permit_no,             --col
                q1.issue_date            AS issue_date,            --col
                q1.purpose               AS purpose,               --col
                q1.holder_name           AS holder_name,           --col
                q1.area_desc             AS area_desc,             --col
                q1.wls_comments          AS wls_comments,          --col
                q1.existing_unit_hyphen  AS existing_unit_hyphen,  --col
                q1.permit_holder_address AS permit_holder_address, --col
                q1.multi_non_bkf         AS multi_non_bkf         --col
                -- q2.title                 AS title,                 --col
                -- q2.PLAN                  AS PLAN,                  --col
                -- q2.parcel                AS parcel,                --col
                -- q2.hundred_id            AS hundred_id,            --col
                -- q2.pastoral_block        AS pastoral_block,        --col
                -- q2.pastoral_lease        AS pastoral_lease,        --col
                -- q2.ref_section           AS ref_section            --col
FROM            (
                         SELECT   wp.permit_no,
                                  wp.issue_date,
                                  wp.purpose,
                                  wp.holder_name,
                                  wp.area_desc,
                                  wp.comments AS wls_comments,
                                  wp.wilma_map_100000_no
                                           || '-'
                                           || wp.wilma_dh_seq_no AS existing_unit_hyphen,
                                  To_char(wp.holder_address_1
                                           || '\n'
                                           || wp.holder_address_2
                                           || '\n'
                                           || wp.holder_suburb
                                           || ' '
                                           || wp.holder_state
                                           || ' '
                                           || wp.holder_postcode) AS permit_holder_address,
                                  wp.multiple_non_bkf_wells_flag  AS multi_non_bkf
                         FROM     dhdbview.wp_permit_wls_vw wp
                         WHERE    wp.permit_no >= {permit_no_from} AND wp.permit_no <= {permit_no_to}
                         ORDER BY permit_no ) q1
-- left outer join
--                 (
--                        SELECT document_no,
--                               title_prefix
--                                      || ' '
--                                      || title_volume
--                                      || '/'
--                                      || title_folio AS title,
--                               plan_type
--                                      || ' '
--                                      || plan_no AS PLAN,
--                               parcel_type
--                                      || ' '
--                                      || parcel_no AS parcel,
--                               hundred_id,
--                               pastoral_block,
--                               pastoral_lease,
--                               reference_section AS ref_section
--                        FROM   dhdb.wp_wilma_permit_property_vw ) q2
-- ON              q1.permit_no = q2.document_no
