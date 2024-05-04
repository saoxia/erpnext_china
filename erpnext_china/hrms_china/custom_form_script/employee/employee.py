# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe
from erpnext.setup.doctype.employee.employee import *
from datetime import datetime
import json
from pathlib import Path

class CustomEmployee(Employee):
	def validate(self):
		from erpnext.controllers.status_updater import validate_status

		validate_status(self.status, ["Active", "Inactive", "Suspended", "Left"])

		self.employee = self.name
		self.set_employee_name()
		self.validate_date()
		self.validate_email()
		self.validate_status()
		self.validate_reports_to()
		self.validate_preferred_email()
		
		#定制
		self.set_gender()
		self.set_date_of_birth()
		self.set_city_of_birth()
		self.set_degree()

		if self.user_id:
			self.validate_user_details()
		else:
			existing_user_id = frappe.db.get_value("Employee", self.name, "user_id")
			if existing_user_id:
				remove_user_permission("Employee", self.name, existing_user_id)

	@property
	def custom_age(self):
		id_card = self.custom_chinese_id_number
		if id_card:
			days = datetime.now()-datetime.strptime(f'{id_card[6:10]}-{id_card[10:12]}-{id_card[12:14]}','%Y-%m-%d')
			return  int(days.days/365)

	def set_degree(self):
		d = ['博士研究生','硕士研究生','本科','大专','高中(中专)']
		m = 999
		try:
			for i in self.education:
				m = min(d.index(i.level),m)
			self.custom_degree = d[m]
		except:
			pass
			
	def set_date_of_birth(self):
		id_card = self.custom_chinese_id_number
		try:
			self.date_of_birth = f'{id_card[6:10]}-{id_card[10:12]}-{id_card[12:14]}'
		except:
			pass

	def set_gender(self):
		id_card = self.custom_chinese_id_number
		if id_card:
			gender_id = int(self.custom_chinese_id_number[-2])%2
			if gender_id == 1:
				self.gender = 'Male'
			else:
				self.gender = 'Female'


	def set_city_of_birth(self):
		id_card = self.custom_chinese_id_number
		if id_card:
			with open((Path(__file__).parent / 'china_city_code.json'),'rb') as file:
				china_city_code_json = file.read()
			china_city_code_dict = json.loads(china_city_code_json)
			self.custom_city_of_birth = china_city_code_dict[id_card[:6]]


@frappe.whitelist()
def get_employee_tree(parent=None, 
					pluck='email',
					orient='list',
					levle=None,
					is_root=None,
					use_cache=False):
	
	'''
	注意：io压力增加时添加从缓存中读取的代码

	parent: default None
		用户唯一标识的类型，可以输入str或dict
		key: email|userid|username
		value: 唯一标识的值

	pluck: default 'email' 返回的字段名
		email|userid|username

	orient: list|dict , 是否返回树状结构

	levle: all|int ,返回多少层级的信息

	is_root: False
	'''
	if is_root:
		# 树的最顶点
		employee = 'HR-EMP-00002'
	elif '@' in parent:
		# 邮箱地址拿第一个员工编号
		filters = {'user_id': parent, 'status': 'Active'}
		employee = frappe.get_all('Employee',filters=filters,pluck='employee')
		employee = employee[0]
	else:
		employee = parent

	# 递归函数来获取下级employee
	def get_subordinates(employee):
		subordinates = []

		filters = {'reports_to': employee,
				'status': 'Active'}
		employees = frappe.get_all('Employee',filters=filters,pluck='employee')
		if employees:
			for i in employees:
				subordinates.append(i)
				subordinates += get_subordinates(i)
		return subordinates
	
	subordinates = get_subordinates(employee)
	
	if (pluck == 'email') and (orient == 'list'):
		# 返回email的列表
		filters = {'employee': ['in',subordinates],
				'status': 'Active'}
		subordinates = frappe.get_all('Employee',filters=filters,pluck='user_id')
		
	return subordinates