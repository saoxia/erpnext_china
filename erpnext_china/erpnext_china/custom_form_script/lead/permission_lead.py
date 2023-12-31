# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe


from erpnext_china.erpnext_china.custom_form_script.employee.employee import get_employee_tree

def lead_has_query_permission(user):
	users = get_employee_tree(parent=user)
	users.append(user)
	users_str_tuple = str(tuple(users)).replace(',)',')')

	if frappe.db.get_value('Has Role',{'parent':user,'role':'System Manager'}):
		# 如果角色包含管理员，则看到全量
		conditions = ''
	else:
		# 其他情况则只能看到自己拥有的线索
		# 待添加上级可以看到下级的线索
		# 线索负责人、被分配者都可以看到线索
		users_str_list = str(list(users)).replace("'",'"')
		conditions = f"lead_owner in {users_str_tuple} or JSON_OVERLAPS(_assign,'{users_str_list}')"
	return conditions