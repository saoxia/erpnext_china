# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from erpnext_china.utils.lead_tools import get_doc_or_none
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
	def custom_keyword(self):
		original_lead = get_doc_or_none('Original Leads', {
			'crm_lead': self.name
		})
		if original_lead:
			return original_lead.keyword

	@property
	def custom_search_word(self):
		original_lead = get_doc_or_none('Original Leads', {
			'crm_lead': self.name
		})
		if original_lead:
			return original_lead.search_word

	@property
	def custom_lead_owner_name(self):
		if self.lead_owner:
			lead_owner = get_doc_or_none('User', {
				'name': self.lead_owner
			})
			if lead_owner:
				return lead_owner.first_name

	def before_save(self):
		doc = get_doc_or_none('Lead', self.name)
		if doc:
			self.custom_last_lead_owner = doc.lead_owner
		else:
			self.custom_last_lead_owner = ''

	# webhook 获取字段值函数
	def get_original_lead(self):
		try:
			doc = frappe.get_last_doc('Original Leads', filters={'crm_lead': self.name})
			return doc.name
		except:
			pass
	
	def get_site_url(self):
		try:
			doc = frappe.get_last_doc('Original Leads', filters={'crm_lead': self.name})
			return doc.site_url
		except:
			pass
	
	def get_return_call_url(self):
		try:
			doc = frappe.get_last_doc('Original Leads', filters={'crm_lead': self.name})
			return doc.return_call_url
		except:
			pass