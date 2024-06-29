# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext_china.utils.lead_tools import get_doc_or_none

class AutoAllocationConfig(Document):
	
	@property
	def employee_name(self):
		frappe.get_last_doc('Original Leads', fitlers={'crm_lead': self.name}).name
		if self.employee:
			employee = get_doc_or_none('Employee', {
				'name': self.employee
			})
			if employee:
				return employee.first_name

