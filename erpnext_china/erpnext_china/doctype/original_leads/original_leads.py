# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from erpnext_china.utils.lead_tools import get_doc_or_none

class OriginalLeads(Document):
	
    @property
    def username(self):
        if self.user:
            user = get_doc_or_none('User', self.user)
            if user:
                return user.username


@frappe.whitelist(allow_guest=True)
def set_keyword(**kwargs):
    token = kwargs.get('token')
    if not token or token != 'MwQUQEeNtppaOVOLlxTvwHliSOMvJfwQcbZiCJHniWt':
        return "no token"
    original_leads = frappe.get_all("Original Leads", filters=[["crm_lead", "!=", ""]], fields=["crm_lead", "keyword", "search_word"])
    for ol in original_leads:
        lead = frappe.get_doc("Lead", ol.crm_lead)
        if lead:
            if ol.keyword:
                frappe.db.set_value("Lead", lead.name, "custom_keyword", ol.keyword, update_modified=False)
                frappe.db.commit()
            if ol.search_word:
                frappe.db.set_value("Lead", lead.name, "custom_search_word", ol.search_word, update_modified=False)
                frappe.db.commit()
    return "success"