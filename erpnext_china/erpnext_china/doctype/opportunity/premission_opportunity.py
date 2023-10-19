import frappe

from erpnext_china.erpnext_china.doctype.employee.employee import get_employee_tree

def opportunity_order_has_query_permission(user):
	users = get_employee_tree(parent=user)
	users.append(user)
	users_str = str(tuple(users)).replace(',)',')')

	if frappe.db.get_value('Has Role',{'parent':user,'role':'System Manager'}):
		# 如果角色包含管理员，则看到全量
		conditions = ''
	else:
		# 其他情况则只能看到自己拥有的商机
		# 待添加上级可以看到下级的商机
		users = get_employee_tree(parent=user)
		users = str(tuple(users))
		conditions = f"owner in {users_str}" 
	return conditions