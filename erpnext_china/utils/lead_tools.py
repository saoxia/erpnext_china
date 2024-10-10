
import datetime
import json
import re
import frappe
from urllib.parse import urlparse, parse_qs
from frappe.model.document import Document
from frappe.utils import logger
logger.set_log_level("DEBUG")
logger = frappe.logger("wx-message", allow_site=True, file_count=10)

def get_doc_or_none(doctype: str, kw: dict):
	"""根据kw查找doctype中是否存在记录，如果存在则返回document对象，否则返回None"""
	doc_name = frappe.db.exists(doctype, kw)
	if doc_name:
		doc = frappe.get_doc(doctype, doc_name)
		return doc
	else:
		return None


def get_or_insert_flow_channel_name(flow_channel_name: str, prefix: str):
	"""判断是否已经有当前的流量渠道，没有则格式化后创建"""

	flow_channel_name = format_flow_channel_name(flow_channel_name, prefix)
	lead_source = get_doc_or_none('Lead Source', {
		'source_name': flow_channel_name
	})
	if not lead_source:
		lead_source_data = {
			'doctype': 'Lead Source',
			"source_name": flow_channel_name
		}
		lead_source = frappe.get_doc(lead_source_data).insert(ignore_permissions=True)
	return lead_source.name


def format_flow_channel_name(name: str, prefix: str):
	"""格式化流量渠道名称 
	
		有这种情况：搜索推广 百度搜索推广 字节-今日头条  其他渠道-手动导入

		统一为 百度-搜索推广，字节-今日头条
	"""
	if name.startswith(prefix):
		name = name.replace(prefix, '', 1)
	if name.startswith('-'):
		return prefix + name
	return '-'.join([prefix, name])


def get_username_in_form_detail(kwargs: dict, source: str):
	"""
	提取用户称呼，默认是线索的ID
	:param source: baidu | douyin
	"""
	if source not in ['baidu', 'douyin']:
		return "未知"
	
	if source == 'baidu':
		form_detail = kwargs.get('form_detail')
		username = "匿名"
		# 目前只有solution_type_name是表单的来源才有称呼
		if '表单' in kwargs.get('solution_type_name', '') and form_detail:
			if isinstance(form_detail, str):
				form_detail = json.loads(form_detail)
			if isinstance(form_detail, list):
				for item in form_detail:
					if item.get('type') == 'name' and item.get('value'):
						username = item.get('value')
						break
		return username

	return kwargs.get('name', '匿名') or "匿名"


def get_or_insert_crm_lead(
		lead_name, source, phone:str, mobile:str, wx:str, 
		city, state, original_lead_name, commit_time, keyword='', search_word='', product_category='',
		auto_allocation=False, bd_account=None, dy_account=None, country='China'):
	"""
	如果存在返回doc，并添加评论有新的原始线索关联过来了，不存在则创建

	:param lead_name: 线索客户称呼
	:param source: 线索来源
	:param phone: 电话
	:param mobile: 手机号
	:param wx: 微信号
	:param city: 市
	:param state: 省
	:param country: 国家
	:param original_lead_name: 创建当前线索的原始线索name
	:param bd_account: 百度平台账户
	:param dy_account: 飞鱼平台账户
	:param auto_allocation: 是否自动分配
	"""
	phone = str(phone).replace(' ', '')
	mobile = str(mobile).replace(' ', '')
	wx = str(wx).replace(' ', '')
	# 如果phone、mobile、wx都没有，则不需要创建CRM线索
	if not any([phone, mobile, wx]):
		return None

	links = get_single_contact_info(phone, mobile, wx)
	# 如果联系方式和客户中已经存在的联系方式重复了，则不创建CRM线索
	records = frappe.get_all("Customer Contact Item", filters=[
		{'contact_info': ['in', links]}
	])
	if len(records) > 0:
		frappe.msgprint("当前联系方式已经存在客户中！")
		return None
	
	or_filters = [
		{'phone': ['in', links]},
		{'mobile_no': ['in', links]},
		{'custom_wechat': ['in', links]}
	]
	# 检查是否存在匹配的线索
	records = frappe.get_all("Lead", or_filters=or_filters)
	if len(records) > 0:
		record = records[0]
		record = frappe.get_doc("Lead", record.name)
		# 已经存在相同联系方式的线索，给个评论提示一下
		insert_crm_note(f"有新的原始线索:【{original_lead_name}】关联到当前线索", record.name)
	else:
		territory = get_system_territory(city or state or country)
		# 构造新记录的数据
		crm_lead_data = {
			'doctype': 'Lead',
			'lead_name': lead_name,
			'source': source,
			'phone': phone or '',
			'mobile_no': mobile or '',
			'custom_wechat': wx or '',
			'city': city,
			'state': state,
			'country': country,
			'territory': territory,
			'custom_employee_baidu_account': bd_account,
			'custom_employee_douyin_account': dy_account,
			'custom_original_lead_name': original_lead_name,
			'lead_owner': '', # 这个给个默认线索负责人为空
			'custom_lead_owner_employee': '',
			'custom_auto_allocation': auto_allocation,
			'custom_product_category': product_category,
			'custom_last_lead_owner': '',
			'custom_commit_time': commit_time,  # 线索提交到平台的时间
			'custom_keyword': keyword,
			'custom_search_word': search_word,
		}
		# 插入新记录
		record = frappe.get_doc(crm_lead_data).insert(ignore_permissions=True)
	return record


def get_system_territory(territory: str):
	if territory == 'China':
		return '中国'
	if territory:
		like_pattern = f"%{territory}%"
		territories = frappe.get_all(
			'Territory',
			filters=[
				['territory_name', 'like', like_pattern]
			]
		)
		if len(territories) > 0:
			territory = territories[0].name
			return territory
	return None

def insert_crm_note(note: str, parent: str):
	try:
		note_data = {
			'doctype': 'CRM Note',
			'note': note,
			'added_by': frappe.session.user,
			'added_on': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			'parent': parent,
			'parentfield': 'notes',
			'parenttype': 'Lead'
		}
		frappe.get_doc(note_data).insert(ignore_permissions=True)
	except:
		pass


def remove_whitespace(s):
	if not s:
		return ''
	# 使用正则表达式替换所有空白字符
	return re.sub(r'\s+', '', str(s))


def get_single_contact_info(p, m, wx):
	links = list(set([i for i in [p, m, wx] + re.findall(r'\d+', wx or '')  if (i and len(str(i))>5)]))
	if len(links) == 0:
		frappe.throw("联系方式格式错误！")
	return links

def add_log(user:str, phone:str, target_type:str, target_name:str, lead: str='', original_lead:str=''):
	if not user:
		user = frappe.session.user
	try:
		if not original_lead:
			doc = frappe.get_doc({
				'doctype': 'Readd Contact Log',
				'created_by': frappe.session.user,
				'contact_info': phone,
				'target_type': target_type,
				'target_name': target_name,
				'lead': lead
			}).insert(ignore_permissions=True)
			frappe.db.commit()
			return doc
	except:
		pass

def url_params_to_dict(url: str):
	parsed_url = urlparse(url)
	query_params = parse_qs(parsed_url.query)
	params_dict = {k: v[0] for k, v in query_params.items()}  # 假设每个参数只有一个值
	return params_dict


def get_fid(url: str):
	if not url:
		return None
	params_dict = url_params_to_dict(url)
	return params_dict.get('fid', None)


def save_message(data:dict, raw_request: str):

	wecom_user_id = data.get('UserID')
	users = frappe.db.get_all('User', or_filters=[
		['custom_wecom_uid', '=', wecom_user_id],
		['name', '=', wecom_user_id]
	])
	user_name = None
	if len(users) > 0:
		user_name = users[0].name
	message_data = {
		'doctype': 'WeCom Message',
		'change_type': data.get('ChangeType'),
		'create_time': datetime.datetime.fromtimestamp(int(data.get('CreateTime'))),
		'user': user_name,
		'wecom_user_id': wecom_user_id,
		'external_user_id': data.get('ExternalUserID'),
		'state': data.get('State'),
		'raw_request': raw_request
	}
	doc = frappe.get_doc(message_data).insert(ignore_permissions=True)
	return doc



def create_crm_lead_by_message(message, original_lead, wx_nickname='企微客户'):
	try:

		# 设置线索创建人
		frappe.set_user(original_lead.owner)
		
		# 设置CRM线索的负责员工
		if message.user:
			employee_user = message.user
		else:
			employee_user = original_lead.owner
		employee = frappe.db.get_value('Employee', {"user_id": employee_user})
		territory = get_system_territory(original_lead.area or original_lead.area_province or 'China')
		
		# 创建CRM线索
		crm_lead_data = {
			'doctype': 'Lead',
			'lead_name': '企微客户',
			'source': '百度-' + original_lead.flow_channel_name,
			'phone': '',
			'mobile_no': '',
			'custom_wechat': '',
			'city': original_lead.area,
			'state': original_lead.area_province,
			'country': 'China',
			'territory': territory,
			'custom_employee_baidu_account': original_lead.employee_baidu_account,
			'custom_employee_douyin_account': None,
			'custom_original_lead_name': original_lead.name,
			'lead_owner': employee_user,
			'custom_lead_owner_employee': employee,
			'custom_auto_allocation': False,
			'custom_product_category': original_lead.product_category,
			'custom_last_lead_owner': '',
			'custom_commit_time': original_lead.commit_time or original_lead.created_datetime,  # 线索提交到平台的时间
			'custom_keyword': original_lead.keyword,
			'custom_search_word': original_lead.search_word,
			'custom_wechat_nickname': wx_nickname,
			'custom_external_userid': message.external_user_id
		}
		lead = frappe.get_doc(crm_lead_data).insert(ignore_permissions=True)
		message.created_by = original_lead.owner
		message.lead = lead.name
		message.save(ignore_permissions=True)

		original_lead.crm_lead = lead.name
		original_lead.save(ignore_permissions=True)
	except Exception as e:
		logger.error(e)


def search_original_lead(state):
	original_lead_name = frappe.db.get_value("Original Leads", filters=[
		["bd_vid", 'like', '%'+state+'%'],
		['solution_type', '=', 'wechat'],
		['crm_lead', '=' ,None],
	], order_by="commit_time desc")
	original_lead = None
	if original_lead_name:
		original_lead = frappe.get_doc("Original Leads", original_lead_name)
	return original_lead


def search_wecom_message(bd_vid):
	state = 'BD' + bd_vid[:30]
	message_name = frappe.db.get_value("WeCom Message", filters=[
		['state', 'like', '%'+state+'%'],
		['lead', '=', None]
	])
	message = None
	if message_name:
		message = frappe.get_doc("WeCom Message", message_name)
	return message

