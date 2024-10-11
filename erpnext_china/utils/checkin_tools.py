import json
import frappe


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


def save_group(group_id, group_name, group_json):
	doc = frappe.new_doc("Checkin Group")
	doc.group_id = group_id
	doc.group_name = group_name
	doc.raw = group_json
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


def update_group(group_id, group_name, group_json):
	doc = frappe.get_doc("Checkin Group", group_id)
	doc.group_name = group_name
	doc.raw = group_json
	doc.save(ignore_permissions=True)


def delete_group(group_id):
	doc = frappe.get_cached_doc("Checkin Group", group_id)
	# 恢复标签状态为未关联
	for tag in doc.tags:
		tag = frappe.get_cached_doc("Checkin Tag", tag.tag)
		tag.linked = 0
		tag.save(ignore_permissions=True)
	doc.delete(ignore_permissions=True)

def process_group(groups):
	dict_groups = {str(group['groupid']): group for group in groups}
	groups_id = set(dict_groups.keys())
	local_groups_id = set(i for i in frappe.get_all("Checkin Group", pluck='group_id'))

	# 企微存在但是本地不存在，则新增本地
	will_add = groups_id - local_groups_id
	for group_id in will_add:
		group = dict_groups[group_id]
		save_group(group_id, group['groupname'], json.dumps(group, ensure_ascii=False))

	# 本地存在，企微不存在，则删除本地
	will_delete = local_groups_id - groups_id
	for group_id in will_delete:
		delete_group(group_id)

	# 共同存在的，则更新规则
	will_update = groups_id & local_groups_id
	for group_id in will_update:
		group = dict_groups[group_id]
		update_group(group_id, group['groupname'], json.dumps(group, ensure_ascii=False))
	frappe.db.commit()

def save_tag(tag_id, tag_name, raw):
	doc = frappe.new_doc("Checkin Tag")
	doc.tag_id = tag_id
	doc.tag_name = tag_name
	doc.raw = raw
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
	
def update_tag(tag_id, tag_name, raw):
	doc = frappe.get_doc("Checkin Tag", tag_id)
	doc.tag_name = tag_name
	doc.raw = raw
	doc.save(ignore_permissions=True)

def delete_tag(tag_id):
	# 首先要断开与考勤规则的联系
	group_names = frappe.get_all("Checkin Staff Tag", filters={
		"tag": tag_id,
		"parenttype": "Checkin Group",
		"parentfield": "tags"
	}, pluck="parent")
	for name in group_names:
		group = frappe.get_cached_doc("Checkin Group", name)
		# 恢复标签状态为未关联
		for index, tag in enumerate(group.tags):
			if str(tag_id) == tag.tag:
				group.tags.pop(index)
		group.save(ignore_permissions=True)
	frappe.delete_doc("Checkin Tag", tag_id, ignore_permissions=True)
