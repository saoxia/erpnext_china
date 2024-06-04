# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class LeadDomainforBaidu(Document):
	pass


@frappe.whitelist(allow_guest=True)
def lead_via_baidu(**kwargs):
	return 'success'