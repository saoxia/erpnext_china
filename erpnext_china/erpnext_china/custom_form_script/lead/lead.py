# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import re
import frappe

from erpnext_china.utils.lead_tools import get_doc_or_none
from erpnext.crm.doctype.lead.lead import Lead
import frappe.utils
from erpnext_china.erpnext_china.custom_form_script.lead.auto_allocation import lead_before_save_handle, check_lead_total_limit, to_public

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

	def validate_single_phone(self):
		links = list(set([i for i in [self.phone, self.mobile_no, self.custom_wechat] + re.findall(r'\d+', self.custom_wechat or '')  if i]))
		or_filters = [
			{'phone': ['in', links]},
			{'mobile_no': ['in', links]},
			{'custom_wechat': ['in', links]}
		]
		filters = {"name": ['!=',self.name]}
		leads = frappe.get_all("Lead",filters=filters, or_filters=or_filters, fields=['name', 'lead_owner'])
		if len(leads) > 0:
			message = []
			for lead in leads:
				message.append(f'{lead.name}')
			message = ', '.join(message)
			frappe.throw(f"当前已经存在相同联系方式的线索: {frappe.bold(message)}", title='线索重复')

	def set_contact_info(self):
		if not any([self.phone, self.mobile_no, self.custom_wechat]):
			frappe.throw(f"联系方式必填")
		
		if self.phone:
			self.phone = str(self.phone).replace(' ','')
		if self.mobile_no:
			self.mobile_no = str(self.mobile_no).replace(' ','')
		if self.custom_wechat:
			self.custom_wechat = str(self.custom_wechat).replace(' ','')

	def validate(self):
		super().validate()
		self.set_contact_info()
		self.validate_single_phone()

	@property
	def custom_lead_owner_name(self):
		if self.lead_owner:
			lead_owner = get_doc_or_none('User', {
				'name': self.lead_owner
			})
			if lead_owner:
				return lead_owner.first_name
	
	def get_original_lead(self):
		original_leads = frappe.get_list('Original Leads', filters={'crm_lead': self.name}, order_by="creation")
		if len(original_leads) > 0:
			return frappe.get_doc('Original Leads', original_leads[0].name)
		return None
	
	@property
	def custom_original_lead_name(self):
		doc = self.get_original_lead()
		if doc:
			return doc.name

	@property
	def custom_site_url(self):
		doc = self.get_original_lead()
		if doc:
			return doc.site_url
	
	@property
	def custom_call_url(self):
		doc = self.get_original_lead()
		if doc:
			return doc.return_call_url

	@property
	def custom_lead_owner_leader_name(self):
		if self.lead_owner:
			employee = get_doc_or_none("Employee", {"user_id": self.lead_owner})
			if employee:
				employee_leader_name = employee.reports_to
				if employee_leader_name:
					employee_leader = frappe.get_doc("Employee", employee_leader_name)
					return employee_leader.user_id
	
	@property
	def custom_created_by(self):
		doc = frappe.get_doc('User', self.owner)
		return doc.first_name

	# 提供给UI Python脚本调用
	def before_save_script(self):
		doc = self
		lead_before_save_handle(doc)

@frappe.whitelist()
def get_lead(**kwargs):
	lead_name = kwargs.get('lead')
	if lead_name:
		lead = frappe.get_doc('Lead', lead_name)
		if not lead.custom_lead_owner_employee or not lead.lead_owner:
			employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, fieldname="name")
			if check_lead_total_limit(employee):
				lead.custom_lead_owner_employee = employee
				lead.lead_owner = frappe.session.user
				lead.save(ignore_permissions=True)
				return 200
			else:
				frappe.msgprint("客保数量已到限制，请放弃一些线索后再来认领吧！")
		else:
			frappe.msgprint("当前线索已经存在负责人，不可再次认领！")


@frappe.whitelist()
def give_up_lead(**kwargs):
	lead_name = kwargs.get('lead')
	if lead_name:
		lead = frappe.get_doc('Lead', lead_name)
		to_public(lead)
		lead.save(ignore_permissions=True)
		return 200


@frappe.whitelist()
def get_employee_lead_total(**kwargs):
	obj = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["name", "custom_lead_total"], as_dict=True)
	if not obj:
		value = 0
	else:
		count = frappe.db.count("Lead", {
			"custom_lead_owner_employee": obj.name,
			"status": ["!=", "Converted"]
		})
		value = (obj.custom_lead_total or 0) - count
	
	return {
		"value": value,
		"fieldtype": "Int",
		"route_options": {},
		"route": []
	}