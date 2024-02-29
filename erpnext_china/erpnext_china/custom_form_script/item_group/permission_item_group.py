import frappe

from erpnext_china.hrms_china.custom_form_script.employee.employee import get_employee_tree

@frappe.whitelist()
def get_item_group_list(parent):
    def get_subordinates(parent):
        subordinates = []

        filters = {'parent_item_group': parent}
        item_groups = frappe.get_all('Item Group',filters=filters,pluck='item_group_name')

        if item_groups:
            for i in item_groups:
                subordinates.append(i)
                subordinates += get_subordinates(i)
        return subordinates
    subordinates = get_subordinates(parent)
    subordinates.append(parent)
    return subordinates



def has_query_permission(user):

	if frappe.db.get_value('Has Role',{'parent':user,'role':['in',['System Manager']]}):
		# 如果角色包含管理员，则看到全量
		conditions = ''
	elif frappe.db.get_value('Has Role',{'parent':user,'role':['in',['销售']]}):
		# 销售可以看到所有成品
		item_groups = get_item_group_list('成品')
		item_groups_str = str(tuple(item_groups)).replace(',)',')')
		conditions = f"item_group_name in {item_groups_str}" 
	else:
		# 其他情况则只能看到自己,上级可以看到下级
		users = get_employee_tree(parent=user)
		users.append(user)
		users_str = str(tuple(users)).replace(',)',')')
		conditions = f"owner in {users_str}" 
	return conditions

def has_permission(doc, user, permission_type=None):
	if frappe.db.get_value('Has Role',{'parent':user,'role':['in',['System Manager','销售会计','销售支持']]}):
		# 如果角色包含管理员，则看到全量
		return True
	elif frappe.db.get_value('Has Role',{'parent':user,'role':['in',['销售']]}):
		# 销售可以看到所有成品组
		item_groups = get_item_group_list('成品')
		if doc.item_group_name in item_groups:
			return True
		else:
			return False
	else:
		# 其他情况则只能看到自己,上级可以看到下级
		users = get_employee_tree(parent=user)
		users.append(user)
		if doc.owner in users:
			return True
		else:
			return False