import frappe

from erpnext_china.hrms_china.custom_form_script.employee.employee import get_employee_tree

def sales_order_has_query_permission(user):
	users = get_employee_tree(parent=user)
	users.append(user)
	users_str = str(tuple(users)).replace(',)',')')

	if frappe.db.get_value('Has Role',{'parent':user,'role':['in',['System Manager','销售会计','销售支持']]}):
		# 如果角色包含管理员，则看到全量
		conditions = ''
	else:
		# 其他情况则只能看到自己拥有的销售订单
		# 待添加上级可以看到下级的销售订单
		users = get_employee_tree(parent=user)
		users = str(tuple(users))
		conditions = f"owner in {users_str}" 
	return conditions