import re
import frappe
import requests


class Link:
	def __init__(self, 
				link_name: str = '', 
				user_list: list[str] = [], 
				department_list: list[int] = [],
				skip_verify: bool = True,
				priority_type: int = 1,
				priority_userid_list: list[str] = [],
				):
		self.link_name = self.clean_string(link_name)
		self.priority_type = priority_type
		self.user_list = user_list
		self.department_list = department_list
		self.skip_verify = skip_verify
		self.priority_userid_list = priority_userid_list
		self.validate()

	def clean_string(self, string):
		if not string:
			return ''
		return re.sub(r'\s+', '', str(string))
	
	def validate(self):
		if not self.link_name:
			raise frappe.ValidationError("The link_name is required!")

		if len(self.user_list) == 0 and len(self.department_list) == 0:
			raise frappe.ValidationError("The lengths of user_list and department_list cannot both be 0!")
		
		if len(self.user_list) > 500:
			raise frappe.ValidationError("The length of user_list cannot exceed 500!")
		
		if self.priority_type == 2 and len(self.priority_userid_list) == 0:
			raise frappe.ValidationError("When priority_type is 2, priority_userid_list is required!")
		
		if len(self.priority_userid_list) > 1000:
			raise frappe.ValidationError("The length of priority_userid_list cannot exceed 1000!")

	def base(self):
		return {
			"link_name": self.link_name,
		}

	def simple(self):
		base = self.base()
		base.update({
			"range": {
				"user_list": self.user_list
			}
		})
		return base

	def full(self):
		base = self.base()
		base.update({
			"range": {
				"user_list": self.user_list,
				"department_list": self.department_list
			},
			"skip_verify": self.skip_verify,
			"priority_option": {
				"priority_type": self.priority_type,
				"priority_userid_list": self.priority_userid_list
			}
		})
		return base


class WXApi:

	urls = {
		"list_link": 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/customer_acquisition/list_link?access_token=',
		'get': 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/customer_acquisition/get?access_token=',
		'create_link': 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/customer_acquisition/create_link?access_token=',
		'update_link': 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/customer_acquisition/update_link?access_token=',
		'delete_link': 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/customer_acquisition/delete_link?access_token='
	}

	def get_url(self, key):
		access_token = self.get_access_token()
		return self.urls[key] + access_token

	def get_api_setting(self):
		doc = frappe.get_doc("WeCom MsgApi Setting")
		return doc.token, doc.key

	def get_wecom_setting(self):
		doc = frappe.get_doc("WeCom Setting")
		return doc

	def get_access_token(self):
		doc = self.get_wecom_setting()
		return doc.access_token

	def customer_acquisition_list_link(self, limit: int, cursor: str=''):
		"""
		企业可通过此接口获取当前仍然有效的获客链接

		:param limit: 返回的最大记录数，整型，最大值100
		:param cursor: 用于分页查询的游标，字符串类型，由上一次调用返回，首次调用可不填
		"""
		
		url = self.get_url('list_link')
		data = {
			'limit': limit,
			'cursor': cursor
		}
		resp = requests.post(url, json=data)
		result = resp.json()
		if result.get('errcode') == 0:
			return result
		return None
	

	def customer_acquisition_get(self, link_id: str):
		"""
		企业可通过此接口根据获客链接id获取链接配置详情

		:param link_id: 获客链接ID，必填
		"""
		url = self.get_url('get')
		data = {
			'link_id': link_id
		}
		resp = requests.post(url, json=data)
		result = resp.json()

	def customer_acquisition_create_link(self, link_name:str, user_list:list[str] = []):
		"""
		企业可通过此接口创建新的获客链接

		:param link_name: 获客连接名称，必填
		:param user_list: 此获客链接关联的userid列表，最多500人
		"""
		url = self.get_url('create_link')
		data = Link(link_name=link_name, user_list=user_list).simple()
		resp = requests.post(url, json=data)
		result = resp.json()

	def customer_acquisition_update_link(self, link_id: str, user_list: list[str] = []):
		"""
		企业可通过此接口编辑获客链接，修改获客链接的关联范围或修改获客链接的名称

		:param link_id: 获客连接id，必填
		:param user_list: 关联的员工id列表
		"""
		url = self.get_url('update_link')
		data = {
			'link_id': link_id,
			"range": {
				"user_list": user_list
			}
		}
		resp = requests.post(url, json=data)
		result = resp.json()

	def customer_acquisition_delete_link(self, link_id: str):
		"""
		企业可通过此接口删除获客链接，删除后的获客链接将无法继续使用

		:param link_id: 获客连接id，必填
		"""
		url = self.get_url('delete_link')
		data = {
			'link_id': link_id
		}
		resp = requests.post(url, json=data)
		result = resp.json()