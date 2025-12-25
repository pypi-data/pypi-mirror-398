select distinct
doc.info_type_code as info_type,
doc.comments as info_title,
ref.doc_type_code as ref_type,
ref.doc_ref_id as ref_id,
ref.title as ref_title,
ref.author as ref_author,
ref.publication as ref_publication,
doc.created_by as info_created_by,
doc.creation_date as info_creation_date
from dd_dh_doc doc
join md_reference ref on doc.reference_no = ref.reference_no
join dd_drillhole dh on doc.drillhole_no = dh.drillhole_no
where doc.drillhole_no in {DH_NO}
and dh.deletion_ind = 'N'