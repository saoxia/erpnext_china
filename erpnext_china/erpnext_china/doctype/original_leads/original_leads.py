# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from erpnext_china.utils.lead_tools import get_doc_or_none

class OriginalLeads(Document):
	
    @property
    def username(self):
        if self.user:
            user = get_doc_or_none('User', self.user)
            if user:
                return user.username
