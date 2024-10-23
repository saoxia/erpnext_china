import json
import frappe

def _set_api_group_link(group_doc):
	# 找到相同名称的 api group关联，如果没有找到则设置为空
	api_group_id = frappe.db.get_value("Checkin API Group", filters={"group_name": group_doc.group_name}, fieldname="group_id")
	if api_group_id:
		group_doc.api_group = api_group_id
	else:
		group_doc.api_group = ''
	group_doc.save(ignore_permissions=True)


def _save_local_group(group_id, group_name, group_json):
	doc = frappe.new_doc("Checkin Group")
	doc.group_id = group_id
	doc.group_name = group_name
	doc.raw = group_json
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
	_set_api_group_link(doc)
	

def _update_local_group(group_id, group_name, group_json):
	doc = frappe.get_cached_doc("Checkin Group", group_id)
	doc.group_name = group_name
	doc.raw = group_json
	doc.save(ignore_permissions=True)
	_set_api_group_link(doc)

def _delete_local_group(group_id):
	doc = frappe.get_cached_doc("Checkin Group", group_id)
	# 断开和标签的关联
	for tag in doc.tags:
		tag = frappe.get_cached_doc("Checkin Tag", tag.tag)
		tag.checkin_group = ''
		tag.save(ignore_permissions=True)
	# 断开与api group的链接
	doc.api_group = ''
	doc.delete(ignore_permissions=True)

def _save_api_group(group_id, group_name, group_json):
	doc = frappe.new_doc("Checkin API Group")
	doc.group_id = group_id
	doc.group_name = group_name
	doc.raw = group_json
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)

def _update_api_group(group_id, group_name, group_json):
	doc = frappe.get_cached_doc("Checkin API Group", group_id)
	doc.group_name = group_name
	doc.raw = group_json
	doc.save(ignore_permissions=True)

def _delete_api_group(group_id):
	doc = frappe.get_cached_doc("Checkin API Group", group_id)
	doc.delete(ignore_permissions=True)

def update_api_groups(raw_groups):
	"""增删改API规则"""
	local_groups = set(str(i) for i in frappe.get_all("Checkin API Group", pluck='group_id'))
	dict_groups = {str(group['groupid']): group for group in raw_groups}
	qv_groups = set(dict_groups.keys())

	add_groups = qv_groups - local_groups
	for gid in add_groups:
		group = dict_groups[gid]
		_save_api_group(gid, group['groupname'], json.dumps(group, ensure_ascii=False))

	will_delete = local_groups - qv_groups
	for gid in will_delete:
		_delete_api_group(gid)

	will_update = qv_groups & local_groups
	for gid in will_update:
		group = dict_groups[gid]
		_update_api_group(gid, group['groupname'], json.dumps(group, ensure_ascii=False))

def update_local_groups(raw_groups):
	"""增删改本地规则"""
	local_groups = set(str(i) for i in frappe.get_all("Checkin Group", pluck='group_id'))
	dict_groups = {str(group['groupid']): group for group in raw_groups}
	qv_groups = set(dict_groups.keys())

	add_groups = qv_groups - local_groups
	for gid in add_groups:
		group = dict_groups[gid]
		_save_local_group(gid, group['groupname'], json.dumps(group, ensure_ascii=False))

	will_delete = local_groups - qv_groups
	for gid in will_delete:
		_delete_local_group(gid)

	will_update = qv_groups & local_groups
	for gid in will_update:
		group = dict_groups[gid]
		_update_local_group(gid, group['groupname'], json.dumps(group, ensure_ascii=False))


def _save_tag(tag_id, tag_name, raw):
	doc = frappe.new_doc("Checkin Tag")
	doc.tag_id = tag_id
	doc.tag_name = tag_name
	doc.raw = raw
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)

def _update_tag(tag_id, tag_name, raw):
	doc = frappe.get_cached_doc("Checkin Tag", tag_id)
	doc.tag_name = tag_name
	doc.raw = raw
	doc.save(ignore_permissions=True)

def _delete_tag(tag_id):
	doc = frappe.get_cached_doc("Checkin Tag", tag_id)
	doc.checkin_group = ''
	names = frappe.get_all("Checkin Group Tag", filters={
		"tag": tag_id
    }, pluck="name")
	for name in names:
		frappe.delete_doc("Checkin Group Tag", name, ignore_permissions=True)
	frappe.delete_doc("Checkin Tag", tag_id, ignore_permissions=True)

def update_tags(full_tags: dict, qv_tags: set):
	"""本地不存在的新增，企微不存在的删除本地，都存在则更新"""
	
	local_tags = set([i for i in frappe.get_all("Checkin Tag", pluck='tag_id')])
	
	add_tags = qv_tags - local_tags
	for tid in add_tags:
		tag = full_tags.get(tid, {})
		_save_tag(tid, tag.get("tag_name"), 
			json.dumps([user.get('userid') for user in tag.get('userid_list', [])], ensure_ascii=False)) 
	
	delete_tags = local_tags - qv_tags
	for tid in delete_tags:
		_delete_tag(tid)

	update_tags = qv_tags & local_tags
	for tid in update_tags:
		tag = full_tags.get(tid, {})
		_update_tag(tid, tag.get("tag_name"), 
			  json.dumps([user.get('userid') for user in tag.get('userid_list', [])], ensure_ascii=False))

def delete_checkin_group(local_group_id):
	local_group = frappe.get_cached_doc("Checkin Group", local_group_id)
	api_group_id = local_group.api_group
	_delete_local_group(local_group_id)
	if api_group_id:
		_delete_api_group(api_group_id)
