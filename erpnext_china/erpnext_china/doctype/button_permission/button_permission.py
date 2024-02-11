# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.modules.import_file import get_file_path

class ButtonPermission(Document):
	pass


@frappe.whitelist()
def get_standard_permissions(doctype):
	meta = frappe.get_meta(doctype)
	if meta.custom:
		doc = frappe.get_doc("DocType", doctype)
		return [p.as_dict() for p in doc.permissions]
	else:
		# also used to setup permissions via patch
		path = get_file_path(meta.module, "DocType", doctype)
		return read_doc_from_file(path).get("permissions")

@frappe.whitelist()
def get_button_permission(doctype):
	r = get_standard_permissions(doctype)
	return 'a'