import frappe
import datetime
import json
import requests
import frappe.utils
import xmltodict
import base64
from urllib.parse import urlparse, parse_qs
from werkzeug.wrappers import Response

from . import WXBizMsgCrypt3
from erpnext_china.utils import lead_tools

def get_url_params(kwargs: dict):
	raw_signature = kwargs.get('msg_signature')
	raw_timestamp = kwargs.get('timestamp')
	raw_nonce = kwargs.get('nonce')
	raw_echostr = kwargs.get('echostr', None)
	return raw_signature, raw_timestamp, raw_nonce, raw_echostr

def save_message(data:dict, raw_request: str, state:str):
	if not frappe.db.exists('WeCom Message', {"state": state}):
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
			'state': state,
			'message': json.dumps(data),
			'raw_request': raw_request
		}
		if not user_name:
			message_data.update({
				'error': f'User {wecom_user_id} cannot be found in the system!'
			})
		doc = frappe.get_doc(message_data).insert(ignore_permissions=True)
		frappe.db.commit()
		return doc
		
	return None


def create_crm_lead_by_message(message):
	try:
		# BDxxxxxxx
		state = message.state
		# xxxxxx
		fid = str(state)[2:]
		original_leads = frappe.get_all("Original Leads", fields=['*'], filters={"fid": fid, 'crm_lead': ''})
		if len(original_leads) == 0:
			raise Exception("No original lead!")
		original_lead = original_leads[0]
		
		# 设置线索创建人
		frappe.set_user(original_lead.owner)

		wx_nickname = get_wx_nickname(message.external_user_id)

		# 创建CRM线索
		data = {
			'lead_name': '匿名',
			'source': '百度-' + original_lead.flow_channel_name,
			'phone': '',
			'mobile': '',
			'wx': '企微客户ID:' + message.external_user_id,
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
			raise Exception("No lead created!")
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

		# 给所有的原始线索添加关联
		for olead in original_leads:
			original_lead_doc = frappe.get_doc("Original Leads", olead.name)
			original_lead_doc.crm_lead = lead.name
			original_lead_doc.save(ignore_permissions=True)
	except Exception as e:
		message.error = str(e)
		message.save(ignore_permissions=True)


def qv_original_lead_link_crm_lead(record):
	# 必须有fid
	if not record.fid:
		return
	# 必须【网民微信交互类型】为【微信加粉成功】
	if not record.solution_ref_type_name == '微信加粉成功':
		return
	
	state = 'BD' + record.fid
	try:
		message = lead_tools.get_doc_or_none("WeCom Message", {"state": state})
		# 如果相同fid的回调消息已经创建了CRM lead，则关联上
		if message and message.lead:
			record.crm_lead = message.lead
			record.save(ignore_permissions=True)
	except:
		pass


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
	except:
		return None



@frappe.whitelist(allow_guest=True)
def wechat_msg_callback(**kwargs):
	url = frappe.utils.get_url() + frappe.request.full_path
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
	dict_content = xmltodict.parse(xml_content)
	dict_data = dict_content.get('xml')

	print(dict_data)

	change_type = dict_data.get('ChangeType')
	state = dict_data.get('State')
	# 如果是添加外部联系人并且有渠道参数并且参数开头是BD
	if change_type == 'add_external_contact' and state:
		# 记录此message
		if isinstance(raw_xml_data, str):
			body = raw_xml_data
		if isinstance(raw_xml_data, bytes):
			body = base64.b64encode(raw_xml_data).decode()
		raw_request = {
			"url": url,
			"body": body
		}
		message = save_message(dict_data, json.dumps(raw_request), state)
		# 尝试找到原始线索并创建crm lead
		# 客户每次在落地页添加推广企微时，会发出三个原始线索分别对应【网民微信交互类型】
		# A【微信复制按钮点击】  B【微信调起】  C【微信加粉成功】
		# 以上三个原始线索的【fid】是相同的，但是有创建先后顺序ABC
		# 企微我们只能接收到C的回调消息M
		# 因此我们可以在创建M后就通过参数【State】找到对应的【fid】对应的原始线索，
		# 理论上必有AB可能有C，此时我们就可以创建CRM线索并关联原始线索
		# 然后在原始线索C创建时，尝试去找M并关联M的lead

		# 1、AB创建，M创建，crm_lead创建，M设置lead，AB设置crm_lead，C创建，C设置M的lead
		# 2、ABC创建，M创建，crm_lead创建，M设置lead，ABC设置crm_lead
		if message:
			create_crm_lead_by_message(message)
