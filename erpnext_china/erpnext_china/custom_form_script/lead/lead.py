# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import re
import frappe

from werkzeug.wrappers import Response
from erpnext_china.utils.lead_tools import get_doc_or_none, remove_whitespace, add_log,get_single_contact_info
from erpnext_china.utils.old_system_data import white_list, old_system_contacts
from erpnext_china.utils.wechat import WXBizMsgCrypt3
from erpnext.crm.doctype.lead.lead import Lead
import frappe.utils
from erpnext_china.erpnext_china.custom_form_script.lead.auto_allocation import lead_before_save_handle, check_lead_total_limit, set_last_lead_owner, set_latest_note, to_public

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
		links = get_single_contact_info(self.phone, self.mobile_no, self.custom_wechat)
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
			add_log(frappe.session.user, ','.join(links), 'Lead', lead.name, lead_name, self.custom_original_lead_name)
			frappe.throw(frappe.bold(message), title='线索重复')

	def clean_contact_info(self):
		if not any([self.phone, self.mobile_no, self.custom_wechat]):
			frappe.throw(f"联系方式必填")

		self.phone = remove_whitespace(self.phone)
		self.mobile_no = remove_whitespace(self.mobile_no)
		self.custom_wechat = remove_whitespace(self.custom_wechat)

	def validate(self):
		super().validate()
		self.clean_contact_info()
		self.validate_single_phone()
		self.check_in_old_system()
		self.check_customer_contacts()

	@property
	def custom_lead_owner_name(self):
		if self.lead_owner:
			lead_owner = get_doc_or_none('User', {
				'name': self.lead_owner
			})
			if lead_owner:
				return lead_owner.first_name
	
	def get_original_lead(self):
		if self.custom_original_lead_name:
			return get_doc_or_none("Original Leads", {"name": self.custom_original_lead_name})
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
	
	def before_save(self):
		doc = self
		if self.has_value_changed("lead_owner"):
			set_last_lead_owner(doc)
			if self.get_doc_before_save():
				self.lead_add_comment(f"分配给: {self.lead_owner}")
		if self.has_value_changed("notes"):
			set_latest_note(doc)

	def after_insert(self):
		if self.custom_original_lead_name:
			text=f"初始自动分配给: {self.lead_owner}"
		else:
			text=f"初始手动分配给: {self.lead_owner}"
		self.lead_add_comment(text)
		return super().after_insert()

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
					
					contact_info = ','.join(get_single_contact_info(self.phone, self.mobile_no, self.custom_wechat))
					add_log(user, contact_info, 'Old System', 'Old System', original_lead=self.custom_original_lead_name)
					
					frappe.throw("当前系统中已经存在此联系方式！")
			return True
		# 除了网推管理和管理员外其他人没有编辑联系方式的权限

	def check_customer_contacts(self):
		# 修改联系方式时，判断是否与非当前客户的联系方式重复了
		if self.has_value_changed("phone") or self.has_value_changed("mobile_no") or self.has_value_changed("custom_wechat"):
			if self.has_customer_contact():
				frappe.throw("当前联系方式已经存在客户中！")

	def has_customer_contact(self):
		links = get_single_contact_info(self.phone, self.mobile_no, self.custom_wechat)
		records = frappe.get_all("Customer Contact Item", filters=[
			{'contact_info': ['in', links]},
			{'lead': ['!=', self.name]}
		])
		if len(records) > 0:
			record = records[0]
			
			lead_name = ''
			if not self.is_new():
				lead_name = self.name
			add_log(frappe.session.user, ','.join(links), 'Customer Contact Item', record.name, lead_name, self.custom_original_lead_name)
			
			return True
		return False

	# 重写 has_customer 方法，阻止检查到线索已经关联了客户后修改线索状态为 已转化（Converted）
	def has_customer(self):
		# return frappe.db.get_value("Customer", {"lead_name": self.name})
		return None
	
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


def get_url_params(kwargs: dict):
	raw_signature = kwargs.get('msg_signature')
	raw_timestamp = kwargs.get('timestamp')
	raw_nonce = kwargs.get('nonce')
	raw_echostr = kwargs.get('echostr', None)
	return raw_signature, raw_timestamp, raw_nonce, raw_echostr


@frappe.whitelist(allow_guest=True)
def wechat_msg_callback(**kwargs):
	event = "customer_acquisition"  # 固定事件类型
	msg_type = "event"  # 固定消息类型
	change_types = [
		"friend_request",  # 客户发起好友请求
		"customer_start_chat",  # 成员首次收到客户消息时
	]
	# 验证URL合法性
	api_setting = frappe.get_doc("WeCom MsgApi Setting")
	wecom_setting = frappe.get_doc("WeCom Setting")
	client = WXBizMsgCrypt3.WXBizMsgCrypt(api_setting.token, api_setting.key, wecom_setting.client_id)
	raw_signature, raw_timestamp, raw_nonce, raw_echostr = get_url_params(kwargs)
	# 如果存在 echostr 说明是首次配置发送的验证性请求
	if raw_echostr:
		code, text = client.VerifyURL(raw_signature, raw_timestamp, raw_nonce, raw_echostr)
		return Response(text)
	# 其它的回调事件
	raw_xml_data = frappe.local.request.data
	code, xml_content = client.DecryptMsg(raw_xml_data, raw_signature, raw_timestamp, raw_nonce)
	print(xml_content)
