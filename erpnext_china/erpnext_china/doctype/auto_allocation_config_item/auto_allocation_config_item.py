# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
from erpnext_china.utils.lead_tools import get_doc_or_none
from frappe.model.document import Document


class AutoAllocationConfigItem(Document):

	@property
	def employee_name(self):
		if self.employee:
			employee = get_doc_or_none('Employee', {
				'name': self.employee
			})
			if employee:
				return employee.first_name
	@property
	def leader_name(self):
		if self.leader:
			leader = get_doc_or_none('Employee', {
				'name': self.leader
			})
			if leader:
				return leader.first_name
			
