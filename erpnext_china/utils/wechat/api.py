import frappe
import datetime
import json
import requests
import xmltodict
import base64
from werkzeug.wrappers import Response

from frappe.utils import logger, get_url

from . import WXBizMsgCrypt3
from erpnext_china.utils import lead_tools

logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=10)

def get_url_params(kwargs: dict):
	raw_signature = kwargs.get('msg_signature')
	raw_timestamp = kwargs.get('timestamp')
	raw_nonce = kwargs.get('nonce')
	raw_echostr = kwargs.get('echostr', None)
	return raw_signature, raw_timestamp, raw_nonce, raw_echostr

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



def create_crm_lead_by_message(message, original_lead):
	try:

		# 设置线索创建人
		frappe.set_user(original_lead.owner)
		euid = str(message.external_user_id)
		wx_nickname = get_wx_nickname(euid)

		# 创建CRM线索
		data = {
			'lead_name': '匿名',
			'source': '百度-' + original_lead.flow_channel_name,
			'phone': '',
			'mobile': '',
			'wx': euid[:5] + '*'*5 + euid[-10:],
			'city': original_lead.area,
			'state': original_lead.area_province,
			'original_lead_name': original_lead.name,
			'commit_time': original_lead.commit_time or original_lead.created_datetime,
			'keyword': original_lead.keyword,
			'search_word': original_lead.search_word,
			'auto_allocation': False,
			'bd_account': original_lead.employee_baidu_account,
			'product_category': original_lead.product_category
		}
		lead = lead_tools.get_or_insert_crm_lead(**data)
		if not lead:
			raise Exception("CRM lead creation failed")
		# 设置CRM线索的负责员工
		if message.user:
			employee_user = message.user
		else:
			employee_user = original_lead.owner
		employee = frappe.db.get_value('Employee', {"user_id": employee_user})
		lead.custom_lead_owner_employee = employee
		lead.lead_owner = employee_user
		lead.custom_wechat_nickname = wx_nickname
		lead.custom_external_userid = message.external_user_id
		lead.save(ignore_permissions=True)
		
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

def qv_create_crm_lead(message=None, original_lead=None):
	try:
		if message:
			state = str(message.state)[2:-1]
			if state:
				original_lead_doc = search_original_lead(state)
				if original_lead_doc:
					create_crm_lead_by_message(message, original_lead_doc)
		
		if original_lead:
			bd_vid = original_lead.bd_vid
			if bd_vid:
				message_doc = search_wecom_message(bd_vid)
				if message_doc:
					create_crm_lead_by_message(message_doc, original_lead)
	except Exception as e:
		logger.error(e)
	

def get_wx_nickname(external_user_id):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get'
	wecom_setting = frappe.get_doc("WeCom Setting")
	params = {
		'access_token': wecom_setting.access_token,
		'external_userid': external_user_id
	}
	try:
		resp = requests.get(url, params=params)
		result = resp.json()
		external_contact = result.get('external_contact')
		return external_contact.get('name')
	except Exception as e:
		logger.warning(e)
		return None


def get_raw_request(url, raw_xml_data):
	if isinstance(raw_xml_data, str):
		body = raw_xml_data
	elif isinstance(raw_xml_data, bytes):
		body = base64.b64encode(raw_xml_data).decode()
	else:
		body = ''
	raw_request = {
		"url": url,
		"body": body
	}
	return raw_request


@frappe.whitelist(allow_guest=True)
def wechat_msg_callback(**kwargs):
	url = get_url() + frappe.request.full_path
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
	try:
		code, xml_content = client.DecryptMsg(raw_xml_data, raw_signature, raw_timestamp, raw_nonce)
		if not xml_content:
			logger.warning("xml_content is None")
			return
		
		dict_content = xmltodict.parse(xml_content)
		dict_data = dict_content.get('xml')
		external_user_id = dict_data.get('ExternalUserID')
		change_type = dict_data.get('ChangeType')
		state = dict_data.get('State')

		if change_type == 'add_external_contact' and state and not frappe.db.exists('WeCom Message', {"external_user_id": external_user_id}):
			raw_request = get_raw_request(url, raw_xml_data)
			message = save_message(dict_data, json.dumps(raw_request))
			if message:
				qv_create_crm_lead(message)
			dict_data.update({"record_id": message.name if message else ''})
			logger.info(dict_data)
	except Exception as e:
		logger.error(e)