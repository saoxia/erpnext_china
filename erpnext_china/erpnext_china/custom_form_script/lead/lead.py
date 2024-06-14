# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from erpnext_china.utils.tools import get_doc_or_none
import frappe
from erpnext.crm.doctype.lead.lead import Lead

class CustomLead(Lead):
	def create_contact(self):
		
        # TODO 根据phone WeChat qq等判断联系人是否已经存
		
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"salutation": self.salutation,
				"gender": self.gender,
				"designation": self.job_title,
				"company_name": self.company_name,
				"custom_wechat":self.custom_wechat,
				"custom_qq":self.custom_qq
			}
		)

		if self.email_id:
			contact.append("email_ids", {"email_id": self.email_id, "is_primary": 1})

		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		contact.reload()  # load changes by hooks on contact

		return contact

	@property
	def url(self):
		original_lead = get_doc_or_none('Original Leads', {
			'crm_lead': self.name
		})
		if original_lead:
			return original_lead.site_url
		return 
	
	@property
	def keyword(self):
		original_lead = get_doc_or_none('Original Leads', {
			'crm_lead': self.name
		})
		if original_lead:
			return original_lead.keyword
		return 


