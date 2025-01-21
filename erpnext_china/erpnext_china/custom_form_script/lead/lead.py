# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe
from erpnext_china.utils import lead_tools
from erpnext_china.utils.old_system_data import white_list, old_system_contacts
from erpnext.crm.doctype.lead.lead import Lead
import frappe.utils
from erpnext_china.erpnext_china.custom_form_script.lead import auto_allocation

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
		links = lead_tools.get_single_contact_info(self.phone, self.mobile_no, self.custom_wechat)
		or_filters = [
			{'phone': ['in', links]},
			{'mobile_no': ['in', links]},
			{'custom_wechat': ['in', links]}
		]
		filters = {"name": ['!=',self.name]}
		leads = frappe.get_all("Lead",filters=filters, or_filters=or_filters, fields=['name', 'owner'])
		if len(leads) > 0:
			lead = leads[0]
			first_name = frappe.db.get_value("User", lead.owner, fieldname='first_name')
			message = f'{first_name}: {lead.name}'
			lead_name = ''
			if not self.is_new():
				lead_name = self.name
			lead_tools.add_log(frappe.session.user, ','.join(links), 'Lead', lead.name, lead_name, self.custom_original_lead_name)
			frappe.throw(frappe.bold(message), title='线索重复')

	def clean_contact_info(self):
		self.phone = lead_tools.remove_whitespace(self.phone)
		self.mobile_no = lead_tools.remove_whitespace(self.mobile_no)
		self.custom_wechat = lead_tools.remove_whitespace(self.custom_wechat)
	
	def validate_contact_format(self):
		if not any([self.phone, self.mobile_no, self.custom_wechat]):
			frappe.throw(f"联系方式必填")
		
	def validate(self):
		super().validate()
		self.clean_contact_info()
		# 如果不是企微客户 或者 有联系方式，则判断是否重复
		if not self.custom_external_userid or any([self.phone, self.mobile_no, self.custom_wechat]):
			self.validate_contact_format()
			self.validate_single_phone()
			self.check_in_old_system()
			self.check_customer_contacts()

	@property
	def custom_lead_owner_name(self):
		if self.lead_owner:
			lead_owner = lead_tools.get_doc_or_none('User', {
				'name': self.lead_owner
			})
			if lead_owner:
				return lead_owner.first_name
	
	def get_original_lead(self):
		if self.custom_original_lead_name:
			return lead_tools.get_doc_or_none("Original Leads", {"name": self.custom_original_lead_name})
		return None
	
	# @property
	# def custom_original_lead_name(self):
	# 	doc = self.get_original_lead()
	# 	if doc:
	# 		return doc.name

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
			employee = lead_tools.get_doc_or_none("Employee", {"user_id": self.lead_owner})
			if employee:
				employee_leader_name = employee.reports_to
				if employee_leader_name:
					employee_leader = frappe.get_doc("Employee", employee_leader_name)
					return employee_leader.user_id
	
	@property
	def custom_created_by(self):
		doc = frappe.get_doc('User', self.owner)
		return doc.first_name

	# 提供给UI Python脚本调用，注意这里会在before_save之前调用
	def before_save_script(self):
		self._custom_comment = '手动分配'
		self._rule_name = ''
		auto_allocation.lead_before_save_handle(self)

	def set_note_difference(self):
		if not self.is_new() and self.has_value_changed("notes"):
			try:
				comment = frappe.get_last_doc('Comment', filters={'reference_name': ['=', self.name],'comment_type':'Comment','reference_doctype': 'Lead'})
				last_time = comment.creation
				for note in self.notes:
					if note.is_new():
						note.custom_time_difference = last_time
			except:
				pass
	
	def set_note_type(self):
		for note in self.notes:
			if note.is_new() and not note.custom_note_type:
				user = frappe.get_doc('User', note.added_by)
				if note.added_by in ['jintingyan@zhushigroup.cn', 'wangjiali@zhushigroup.cn']:
					note.custom_note_type = '客服反馈'
				elif user.role_profile_name == '销售':
					note.custom_note_type = '销售反馈'
				elif user.role_profile_name == '网推':
					note.custom_note_type = '网推反馈'
				else:
					note.custom_note_type = '其它'

	def check_lead_source(self):
		user = frappe.get_doc('User', self.owner)
		if self.is_new() and user.role_profile_name == '销售':
			source = frappe.db.get_value('Lead Source', filters={'name': '销售录入'})
			if not source:
				doc = frappe.new_doc('Lead Source')
				doc.source_name = '销售录入'
				doc.custom_sorted_index = 999
				doc.insert(ignore_permissions=True)
			self.source = '销售录入'

	def before_save(self):

		# self.check_lead_source()
		self.set_note_difference()
		
		if not self.custom_original_lead_name:
			self.custom_employee_baidu_account = ''
			self.custom_employee_douyin_account = ''

		if self.has_value_changed("lead_owner"):
			lead_tools.set_last_lead_owner(self)

		if self.has_value_changed("notes"):
			self.set_note_type()
			lead_tools.set_latest_note(self)

		if self.is_new():
			if not self.custom_original_lead_name:
				self._custom_comment = f'初始手动录入，{self._custom_comment}给：{self.lead_owner}，规则：{self._rule_name}'
			else:
				self._custom_comment = f'初始自动录入，自动分配给：{self.lead_owner}，规则：{self._rule_name}'
		else:
			if self.has_value_changed("lead_owner"):
				text = f"{self._custom_comment}给：{self.lead_owner}，规则：{self._rule_name}"
				self.lead_add_comment(text)
				lead_tools.insert_crm_note(self, text, '分配日志')
		
		if self.is_new() and self.source == "业务自录入":
			self.status = "Lead"

	def after_insert(self):
		super().after_insert()
		self.lead_add_comment(self._custom_comment)
		lead_tools.insert_crm_note(self, self._custom_comment, '分配日志', True)

	def lead_add_comment(self, text: str):
		try:
			self.add_comment("Comment", text=text)
		except:
			pass

	def check_in_old_system(self):
		if self.is_new():
			user = frappe.session.user
			if frappe.db.get_value('Has Role',{'parent': user,'role':['in',['System Manager','网络推广管理']]}) or (user in white_list):
				return True
			else:
				if (self.phone in old_system_contacts) or (self.mobile_no in old_system_contacts) or (self.custom_wechat in old_system_contacts):
					
					contact_info = ','.join(lead_tools.get_single_contact_info(self.phone, self.mobile_no, self.custom_wechat))
					lead_tools.add_log(user, contact_info, 'Old System', 'Old System', original_lead=self.custom_original_lead_name)
					
					frappe.throw("当前系统中已经存在此联系方式！")
			return True
		# 除了网推管理和管理员外其他人没有编辑联系方式的权限

	def check_customer_contacts(self):
		# 修改联系方式时，判断是否与非当前客户的联系方式重复了
		if self.has_value_changed("phone") or self.has_value_changed("mobile_no") or self.has_value_changed("custom_wechat"):
			if self.has_customer_contact():
				frappe.throw("当前联系方式已经存在客户中！")

	def has_customer_contact(self):
		links = lead_tools.get_single_contact_info(self.phone, self.mobile_no, self.custom_wechat)
		records = frappe.get_all("Customer Contact Item", filters=[
			{'contact_info': ['in', links]},
			{'lead': ['!=', self.name]}
		])
		if len(records) > 0:
			record = records[0]
			
			lead_name = ''
			if not self.is_new():
				lead_name = self.name
			lead_tools.add_log(frappe.session.user, ','.join(links), 'Customer Contact Item', record.name, lead_name, self.custom_original_lead_name)
			
			return True
		return False

@frappe.whitelist()
def get_lead(**kwargs):
	lead_name = kwargs.get('lead')
	if lead_name:
		lead = frappe.get_doc('Lead', lead_name)
		if not lead.custom_lead_owner_employee or not lead.lead_owner:
			employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, fieldname="name")
			if lead.source == '业务自录入' or auto_allocation.check_lead_total_limit(employee):
				lead.custom_lead_owner_employee = employee
				lead.lead_owner = frappe.session.user
				auto_allocation.to_private(lead)
				lead.save(ignore_permissions=True)
				return 200
			else:
				frappe.msgprint("客保数量已到限制，请放弃一些线索后再来认领吧！")
		else:
			frappe.msgprint("当前线索已经存在负责人，不可再次认领！")


@frappe.whitelist()
def give_up_lead(**kwargs):
	lead_name = kwargs.get('lead')
	content = kwargs.get('content')
	if lead_name:
		lead = frappe.get_doc('Lead', lead_name)
		auto_allocation.to_public(lead)

		if content:
			lead.append("notes", {
				"note": content,
				"custom_note_type": "销售反馈",
				"added_by": frappe.session.user,
				"added_on": frappe.utils.get_datetime()
			})

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
			"status": ["!=", "Converted"],
			"source": ["!=", "业务自录入"]
		})
		value = (obj.custom_lead_total or 0) - count
	
	return {
		"value": value,
		"fieldtype": "Int",
		"route_options": {},
		"route": []
	}

@frappe.whitelist()
def get_viewed_on(**kwargs):
	try:
		lead = kwargs.get('lead')
		lead_owner = kwargs.get('lead_owner')
		doc = frappe.get_last_doc("View Log", filters={"reference_name": lead, "viewed_by": lead_owner}, order_by="creation asc")
		return {"viewed_on": doc.creation}
	except:
		return
