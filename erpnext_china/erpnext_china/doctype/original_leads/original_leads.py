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
    original_leads = frappe.get_all("Original Leads", filters=[["crm_lead", "!=", ""]], fields=["crm_lead", "keyword", "search_word"], order_by="creation desc")
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


@frappe.whitelist(allow_guest=True)
def set_keyword_v2(**kwargs):
    token = kwargs.get('token')
    if not token or token != 'MwQUQEeNtppaOVOLlxTvwHliSOMvJfwQcbZiCJHniWt':
        return "no token"
    leads = frappe.get_all("Lead", fields=["name", "custom_original_lead_name"])
    for lead in leads:
        if lead.custom_original_lead_name:
            original_lead = frappe.get_doc("Original Leads", lead.custom_original_lead_name)
            frappe.db.set_value("Lead", lead.name, "custom_keyword", original_lead.keyword, update_modified=False)
            frappe.db.set_value("Lead", lead.name, "custom_search_word", original_lead.search_word, update_modified=False)
            frappe.db.commit()
    return "success"


@frappe.whitelist(allow_guest=True)
def set_custom_original_lead_name(**kwargs):
    token = kwargs.get('token')
    if not token or token != 'MwQUQEeNtppaOVOLlxTvwHliSOMvJfwQcbZiCJHniWt':
        return "no token"
    leads = frappe.get_all("Lead")
    for lead_name in leads:
        original_leads = frappe.get_all("Original Leads", filters=[["crm_lead", "=", lead_name.name]], fields=["name", "keyword", "search_word"], order_by="creation")
        if len(original_leads) > 0:
            original_lead = original_leads[0]
            frappe.db.set_value("Lead", lead_name.name, "custom_original_lead_name", original_lead.name, update_modified=False)
            frappe.db.commit()
    return "success"