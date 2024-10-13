import traceback
import frappe
import datetime
import json
import requests
import xmltodict
import base64
from werkzeug.wrappers import Response

from frappe.utils import logger, get_url

from . import WXBizMsgCrypt3
from erpnext_china.utils import lead_tools, checkin_tools


logger.set_log_level("DEBUG")
logger = frappe.logger("wx-message", allow_site=True, file_count=10)

def get_url_params(kwargs: dict):
	raw_signature = kwargs.get('msg_signature')
	raw_timestamp = kwargs.get('timestamp')
	raw_nonce = kwargs.get('nonce')
	raw_echostr = kwargs.get('echostr', None)
	return raw_signature, raw_timestamp, raw_nonce, raw_echostr


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


def get_tag_staff(tag_id, access_token):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/get'
	params = {
		'access_token': access_token,
		'tagid': tag_id
	}
	resp = requests.get(url, params=params)
	result = resp.json()
	return result.get('userlist')


def get_checkin_group(access_token: str):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/checkin/getcorpcheckinoption'

	params = {
		'access_token': access_token
	}
	resp = requests.get(url, params=params)
	result = resp.json()
	return result.get('group')


def get_tags(access_token: str):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/list'
	params = {
		'access_token': access_token
	}
	resp = requests.get(url, params=params)
	result = resp.json()
	# tagid  tagname
	return result.get('taglist')



def get_check_in_data(access_token: str, users: list[str], starttime: int, endtime: int, opencheckindatatype:int=3):
	"""
	请求考勤记录
	"""
	url = "https://qyapi.weixin.qq.com/cgi-bin/checkin/getcheckindata?access_token=" + access_token
	# opencheckindatatype 打卡类型。1：上下班打卡；2：外出打卡；3：全部打卡
	data = {
		"opencheckindatatype": opencheckindatatype,
		"starttime": starttime,
		"endtime": endtime,
		"useridlist": users
	}
	res = requests.post(url, json=data)
	result = res.json()
	return result.get('checkindata', [])


def get_departments(access_token: str):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/department/list'
	params = {
		'access_token': access_token
	}
	resp = requests.get(url, params=params)
	result = resp.json()
	return result.get('department')


def get_staff_from_department(department: dict, access_token: str):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist'
	params = {
		'access_token': access_token,
		'department_id': department.get('id')
	}
	resp = requests.get(url, params=params)
	result = resp.json()
	# return result.get('userlist')
	return [
		{
			"user_id": user.get('userid'), 
			"user_name": user.get('name'), 
			"department_id": department.get('id'),
			"department_name": department.get('name')
		} for user in result.get('userlist')
	]

def check_wecom_user(user_id, access_token):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/user/get'

	params = {
		'access_token': access_token,
		'userid': user_id,
	}
	try:
		resp = requests.get(url, params=params)
		result = resp.json()
		# {'errcode': 60111, 'errmsg': 'invalid string value `FuLiJun1`. userid not found', ...}
		# 60111 表示企微没有此用户
		if result.get("errcode") == 60111:
			return False
		return True
	except Exception as e:
		# 如果因为网络问题等因素导致错误，则返回True
		return True


def delete_checkin_group(access_token, group_id):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/checkin/del_checkin_option'
	params = {
		'access_token': access_token
	}
	data = {
		"groupid": group_id,
		"effective_now": True
	}
	resp = requests.post(url, params=params, json=data)
	result = resp.json()
	logger.info(result)

	if result.get('errcode') != 0:
		frappe.throw("考勤规则删除失败！" + result.get('errmsg', ''))


def clean_checkin_group_params(group: dict):
	# wifimac_infos 和 loc_infos必须设置一个
	if not group.get('wifimac_infos', []) and not group.get('loc_infos', []):
		group['loc_infos'] = [
			{
				"lat": 36663583,  # 纬度
				"lng": 117008871,  # 经度
				"loc_title": "绿地中心",
				"loc_detail": "山东省济南市市中区共青团路25号",
				"distance": 100
			}
		]
	# 先清空range
	group['range']['userid'] = []
	group['range']['party_id'] = []
	group['range']['tagid'] = []
	group.pop("create_time", None)
	group.pop("create_userid", None)
	group.pop('update_userid', None)
	group.pop('updatetime', None)
	# ot_info已经被ot_info_v2代替了，参数中有ot_info会报错
	group.pop('ot_info', None)

	# 当checkindate.allow_flex 为false时
	for checkindate in group.get('checkindate', []):
		if not checkindate.get('allow_flex', False):
			checkindate.pop("late_rule", None)
			checkindate.pop('flex_on_duty_time', None)
			checkindate.pop('flex_off_duty_time', None)
			checkindate.pop('max_allow_arrive_early', None)
			checkindate.pop('max_allow_arrive_late', None)

		for checkintime in checkindate.get('checkintime', []):
			if not checkintime.get('allow_rest', False):
				checkintime.pop('rest_begin_time', None)
				checkintime.pop('rest_end_time', None)
	
	# schedulelist
	for schedulelist in group.get('schedulelist', []):
		if not schedulelist.get('allow_flex', False):
			schedulelist.pop('flex_on_duty_time', None)
			schedulelist.pop('flex_off_duty_time', None)
			schedulelist.pop('late_rule', None)
			schedulelist.pop('limit_aheadtime', None)
			schedulelist.pop('limit_offtime', None)
			schedulelist.pop('noneed_offwork', None)
			schedulelist.pop('flex_time', None)
		for time_section in schedulelist.get('time_section', []):
			if not time_section.get('allow_rest', False):
				time_section.pop('rest_begin_time', None)
				time_section.pop('rest_end_time', None)
	
	buka_remind = group.get('buka_remind', {})
	if not buka_remind.get('open_remind', False):
		buka_remind.pop('buka_remind_day', None)
		buka_remind.pop('buka_remind_month', None)
	return group

def create_checkin_group(access_token, group, effective_now=False):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/checkin/add_checkin_option'
	params = {
		'access_token': access_token
	}
	data = {
		'effective_now': effective_now,
		'group': group
	}
	resp = requests.post(url, params=params, json=data)
	result = resp.json()
	logger.info(result)

	if result.get('errcode') != 0:
		frappe.throw("考勤规则创建失败！" + result.get('errmsg', ''))
	

def update_checkin_group(access_token, group: dict, effective_now=False):
	url = 'https://qyapi.weixin.qq.com/cgi-bin/checkin/update_checkin_option'
	params = {
		'access_token': access_token
	}
	data = {
		'effective_now': effective_now,
		'group': group
	}
	resp = requests.post(url, params=params, json=data)
	result = resp.json()
	logger.info(result)

	if result.get('errcode') != 0:
		frappe.throw("考勤规则修改失败！" + result.get('errmsg', ''))


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


def qv_create_crm_lead(message=None, original_lead=None):
	try:
		if message:
			state = str(message.state)[2:-1]
			if state:
				original_lead_doc = lead_tools.search_original_lead(state)
				if original_lead_doc:
					euid = str(message.external_user_id)
					wx_nickname = get_wx_nickname(euid)
					lead_tools.create_crm_lead_by_message(message, original_lead_doc, wx_nickname)
		
		if original_lead:
			bd_vid = original_lead.bd_vid
			if bd_vid:
				message_doc = lead_tools.search_wecom_message(bd_vid)
				if message_doc:
					euid = str(message_doc.external_user_id)
					wx_nickname = get_wx_nickname(euid)
					lead_tools.create_crm_lead_by_message(message_doc, original_lead, wx_nickname)
	except Exception as e:
		logger.error(e)


def update_tags(access_token):

	tags = get_tags(access_token)
	full_tags = {}
	for tag in tags:
		tag_id = tag.get('tagid')
		full_tags[str(tag_id)] = {
			"tag_name": tag.get('tagname'),
			"userid_list": get_tag_staff(tag_id, access_token)
		}
	qv_tags = set(full_tags.keys())
	checkin_tools.update_tags(full_tags, qv_tags)

def update_groups(access_token):
	# 更新考勤规则
	groups = get_checkin_group(access_token)
	# 这是企微中通过API创建的规则
	api_groups = [group for group in groups if not group.get('create_userid', None)]
	# 这是企微中手动创建的规则
	origin_groups = [group for group in groups if group.get('create_userid', None)]
	checkin_tools.update_api_groups(api_groups)
	checkin_tools.update_local_groups(origin_groups)

@frappe.whitelist(allow_guest=True)
def wecom_to_ebc():
	try:
		setting = frappe.get_cached_doc("WeCom Setting")
		access_token = setting.access_token
		update_tags(access_token)
		update_groups(access_token)
		frappe.db.commit()
	except Exception as e:
		logger.error(traceback.format_exc())
		frappe.db.rollback()

@frappe.whitelist(allow_guest=True)
def group_write_into_wecom(**kwargs):
	effective_now = kwargs.get('effective_now', '0')
	if effective_now == '0':
		effective_now = False
	else:
		effective_now = True
	group_id = kwargs.get('group_id')
	setting = frappe.get_cached_doc("WeCom Setting")
	access_token = setting.access_token

	group_doc = frappe.get_cached_doc("Checkin Group", group_id)
	# 找到当前规则下的考勤标签
	staff = set()
	for t in group_doc.tags:
		tag = frappe.get_cached_doc("Checkin Tag", t.tag)
		staff = staff.union(set(json.loads(tag.raw)))
	# 去除无效的字段
	group_data = clean_checkin_group_params(json.loads(group_doc.raw))
	group_data['range']['userid'] = list(staff)
	
	# 如果已经是创建过的考勤，则更新
	if group_doc.api_group:
		# 这里要使用手动规则对应的API规则的ID
		group_data['groupid'] = group_doc.api_group
		update_checkin_group(access_token, group_data, effective_now)
	else:
		group_data.pop('groupid')
		create_checkin_group(access_token, group_data, effective_now)
	frappe.enqueue('erpnext_china.utils.wechat.api.wecom_to_ebc', job_id=group_id, deduplicate=True)
	frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def delete_group(**kwargs):
	group_id = kwargs.get('group_id')
	if not group_id:
		frappe.throw("必须选择一个规则")
	setting = frappe.get_cached_doc("WeCom Setting")
	access_token = setting.access_token
	# 删除企微API创建的规则
	group = frappe.get_cached_doc("Checkin Group", group_id)
	if group.api_group:
		delete_checkin_group(access_token, group.api_group)
		checkin_tools.delete_checkin_group(group_id)
	frappe.enqueue('erpnext_china.utils.wechat.api.wecom_to_ebc', job_id=group_id, deduplicate=True)
	frappe.db.commit()


def group_write_to_wecom_by_tag(tag_id):
	"""将关联到此标签的规则更新userid到企微"""
	local_group_id = frappe.db.get_value("Checkin Staff Tag", filters={
		"parentfield": "tags",
		"parenttype": "Checkin Group",
		"tag": tag_id
	}, fieldname='parent')

	# 如果标签没有和规则关联就退出
	if not local_group_id:
		return
	
	tag = frappe.get_doc("Checkin Tag", tag_id)
	users = json.loads(tag.raw)

	setting = frappe.get_cached_doc("WeCom Setting")
	access_token = setting.access_token

	# 找到对应的API group
	local_group = frappe.get_cached_doc("Checkin Group", local_group_id)
	if not local_group.api_group:
		return
	group = {
		"groupid": int(local_group.api_group),
		"range": {
			"userid": users
		}
	}
	update_checkin_group(access_token, group, effective_now=True)


def checkin_enqueue_task(tag_id):
	"""
	标签员工变化事件发生时，进更新企微规则对应的员工
	"""
	# 更新标签和规则：将标签对应的员工同步过来
	wecom_to_ebc()
	# 将标签对应的规则更新对应的员工
	group_write_to_wecom_by_tag(tag_id)
	# 将更新后的API规则同步下来
	wecom_to_ebc()


@frappe.whitelist(allow_guest=True)
def wechat_msg_callback(**kwargs):
	url = get_url() + frappe.request.full_path
	# 验证URL合法性
	api_setting = frappe.get_cached_doc("WeCom MsgApi Setting")
	wecom_setting = frappe.get_cached_doc("WeCom Setting")
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
		change_type = dict_data.get('ChangeType')
		
		# 当标签发生变化时，更新系统的考勤标签、考勤规则
		if change_type == 'update_tag':
			tag_id = dict_data.get('TagId')
			tag_doc = frappe.get_cached_doc("Checkin Tag", tag_id)
			if str(tag_doc.tag_name).startswith('考勤'):
				# checkin_enqueue_task(tag_id=tag_doc.tag_id)
				frappe.enqueue('erpnext_china.utils.wechat.api.checkin_enqueue_task', tag_id=tag_doc.tag_id, job_id=raw_signature, deduplicate=True)
			return

		# 如果是获客助手新增客户
		elif change_type == 'add_external_contact':
			external_user_id = dict_data.get('ExternalUserID')
			state = dict_data.get('State')
			msg = frappe.db.exists('WeCom Message', {"external_user_id": external_user_id})
			if  state and msg is None:
				raw_request = get_raw_request(url, raw_xml_data)
				message = lead_tools.save_message(dict_data, json.dumps(raw_request))
				if message:
					qv_create_crm_lead(message)
				dict_data.update({"record_id": message.name if message else ''})
			logger.info(dict_data)
			frappe.db.commit()

			return
	except Exception as e:
		logger.error(e)


@frappe.whitelist()
def msg_create_lead_handler(**kwargs):
	original_lead_name = kwargs.get('original_lead')
	message_name = kwargs.get('message')
	if not original_lead_name or not message_name:
		raise frappe.ValidationError("original lead and message are required!")
	try:
		original_lead_doc = frappe.get_doc("Original Leads", original_lead_name)
		message_doc = frappe.get_doc("WeCom Message", message_name)
		euid = str(message_doc.external_user_id)
		wx_nickname = get_wx_nickname(euid)
		lead_tools.create_crm_lead_by_message(message_doc, original_lead_doc, wx_nickname)
	except Exception as e:
		logger.error(e)
		raise frappe.ValidationError("crm lead creation failed!")