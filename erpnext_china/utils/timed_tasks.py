import math
import hashlib
from datetime import datetime
import frappe.utils
import requests
import frappe

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


def add_employee_checkin_log(check_in_data, code, employee):
	"""
	写入考勤记录
	"""
	checkin_time = datetime.fromtimestamp(check_in_data.get('checkin_time'))
	exception_type = check_in_data.get('exception_type')
	doc_data = {
		"doctype": "Employee Checkin Log",
		"employee": employee,
		"checkin_time": checkin_time,
		"code": code,
		"exception_type": exception_type
	}

	checkin_type = check_in_data.get('checkin_type')
	address = ','.join([check_in_data.get('location_title', ''), check_in_data.get('location_detail', '')])
	if checkin_type in ['上班打卡', '下班打卡']:
		doc_data.update({
			"location_or_device_id": address,
			"log_type": '内勤-考勤机',
		})
	else:
		doc_data.update({
			"address": address,
			"longitude": check_in_data.get('lng'),
			"latitude": check_in_data.get('lat'),
			"log_type": '外勤-手机定位',
		})
	doc = frappe.get_doc(doc_data).insert(ignore_permissions=True)
	frappe.db.commit()


def get_today_timestamp():
	"""
	返回每天00:00:00 到当前的两个时间点
	"""
	now = datetime.now()
	year = now.year
	month = now.month
	day = now.day
	start_time = int(datetime(year, month, day, 0, 0, 0).timestamp())
	end_time = int(now.timestamp())
	return start_time, end_time


def get_temp_users():
	"""
	没有梳理好Employee和User中的数据时，暂时用
	"""
	users_id = [
		"bianxuezhen@zhushigroup.cn",
		"wangzhenhua@zhushigroup.cn",
		"lichengxi@zhushigroup.cn",
		"limingyuan@zhushigroup.cn",
		"lixiulu@zhushigroup.cn",
		"houjun@zhushigroup.cn",
		"dongjuanjuan@zhushigroup.cn",
		"liziyuan@zhushigroup.cn",
		"yangzhen@zhushigroup.cn",
		"liuchao@zhushigroup.cn"
	]
	users = []
	for uid in users_id:
		user = {"user": uid, "employee": "", "wecom": uid}
		custom_wecom_uid = frappe.db.get_value("User", uid, fieldname='custom_wecom_uid')
		if custom_wecom_uid:
			user.update({"wecom": custom_wecom_uid})
		employee_name = frappe.db.get_value("Employee", {"user_id": uid}, fieldname="name")
		if employee_name:
			user.update({"employee": employee_name})
		users.append(user)
	return users


def get_all_active_users():
	employees = frappe.get_all("Employee", filters={"status": 'Active'}, fields=["name", "user_id"])
	users = []
	for employee in employees:
		user = {"user": employee.user_id, "employee": employee.name, "wecom": employee.user_id}
		if employee.user_id:
			custom_wecom_uid = frappe.db.get_value("User", employee.user_id, fieldname='custom_wecom_uid')
			if custom_wecom_uid:
				user.update({"wecom": custom_wecom_uid})
			users.append(user)
	return users


def get_user_slices(users):
	# user 每次最多100
	slices = math.ceil(len(users) / 100)
	return [users[i*100:(i+1)*100] for i in range(slices)]


def trans_user_dict(users):
	result = {}
	for user in users:
		result.update({user.get('wecom'): user})
	return result


def has_exists(code):
	return frappe.db.exists("Employee Checkin Log", {"code": code})


def timestamp_to_str(dt:int, fmt: str=r"%Y-%m-%d %H:%M:%S"):
	return datetime.fromtimestamp(dt).strftime(fmt)


def get_exists_count(users, start_time, end_time):
	count = frappe.db.count("Employee Checkin Log", filters=[
		["checkin_time", "between", [
			timestamp_to_str(start_time), 
			timestamp_to_str(end_time)
		]],
		["employee", 'in', [user.get('employee') for user in users]]
	])
	return count or 0


@frappe.whitelist(allow_guest=True)
def task_get_check_in_data():
	# [{user, employee, wecom}]
	all_users = get_all_active_users()
	# all_users = get_temp_users()
	setting = frappe.get_doc("WeCom Setting")
	access_token = setting.access_token
	
	if not access_token:
		return
	
	start_time, end_time = get_today_timestamp()
	
	# [[0-100],[100-200],[200-267]]
	user_slices = get_user_slices(all_users)
	for users in user_slices:
		results = get_check_in_data(access_token, [user.get("wecom") for user in users], start_time, end_time)
		local_exists_count = get_exists_count(users, start_time, end_time)
		
		# 当日已存在的记录个数和新拉取的数据个数一致说明无变化
		# 避免没有新数据增量出现也会执行has_exists去重操作
		# 过了四个打卡高峰期后，一般不会有新增量出现
		if local_exists_count >= len(results):
			continue
		
		trans_users = trans_user_dict(users)
		for result in results:
			# 这里的userid其实是我们User的custom_wecom_uid
			userid = result.get('userid')
			code = '.'.join([userid, str(result.get('checkin_time'))])

			# 每条数据根据 code 判重，code为索引字段
			if has_exists(code):
				continue

			employee = trans_users.get(userid).get('employee')
			add_employee_checkin_log(result, code, employee)


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


def disable_user(name):
	# 使用管理员账号进行修改
	frappe.set_user('Administrator')
	doc = frappe.get_doc("User", name)
	try:
		doc.enabled = False
		doc.save()
		frappe.db.commit()
	except:  # 有的可能因为信息不全报错
		pass


@frappe.whitelist(allow_guest=True)
def task_check_user_in_wecom():
	users = frappe.get_all("User", filters={"enabled": True}, fields=["name", "custom_wecom_uid"])
	setting = frappe.get_doc("WeCom Setting")
	access_token = setting.access_token
	
	# 预定义白名单
	whitelist = [
		"Administrator",
		"api@api.com",
		"api001@api.com",
		"Guest",
		"admin2@zhushigroup.cn"
	]
	for user in users:
		user_id = user.custom_wecom_uid or user.name
		if user_id not in whitelist and not check_wecom_user(user_id, access_token):
			disable_user(user.name)


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


def save_staff(user_id, user_name, department_id, department_name):
	doc = frappe.new_doc("Checkin Staff")
	doc.user_id = user_id
	doc.user_name = user_name
	doc.department_id = department_id
	doc.department_name = department_name
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


def update_staff(staff):
	for s in staff:
		save_staff(**s)
	frappe.db.commit()


def save_group(group_name, group_id):
	doc = frappe.new_doc("Checkin Group")
	doc.group_id = group_id
	doc.group_name = group_name
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


def update_group(groups):
	for group in groups:
		save_group(group_id=group.get('groupid'), group_name=group.get('groupname'))
	frappe.db.commit()

def save_tag(tag_id, tag_name):
	doc = frappe.new_doc("Checkin Tag")
	doc.tag_id = tag_id
	doc.tag_name = tag_name
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


def update_tag(tags):
	for tag in tags:
		save_tag(tag_id=tag.get('tagid'), tag_name=tag.get('tagname'))
	frappe.db.commit()

def update_staff_tag(staff_id, tag_id):
	doc = frappe.get_cached_doc("Checkin Staff", staff_id)
	doc.append("tags", {
		"tag": tag_id
	})
	doc.save(ignore_permissions=True)


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


def clean_staff():
	frappe.db.delete("Checkin Staff")

def clean_tag():
	frappe.db.delete("Checkin Tag")

def clean_group():
	frappe.db.delete("Checkin Group")

def clean_staff_tag():
	frappe.db.delete("Checkin Staff Tag")
	
def all_clean():
	clean_staff_tag()
	clean_tag()
	clean_group()
	clean_staff()
	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def task_update_wecom_staff():
	setting = frappe.get_doc("WeCom Setting")
	access_token = setting.access_token

	# 清空
	all_clean()

	# 更新员工
	departments = get_departments(access_token)
	for department in departments:
		staff = get_staff_from_department(department, access_token)
		update_staff(staff)

	# # 更新标签
	tags = get_tags(access_token)
	update_tag(tags)

	# 更新标签下的员工
	for tag in tags:
		tag_id = tag.get('tagid')
		staff = get_tag_staff(tag_id, access_token)
		for user in staff:
			update_staff_tag(user.get('userid'), tag_id)

	# # 更新考勤规则
	groups = get_checkin_group(access_token)
	update_group(groups)

	frappe.db.commit()