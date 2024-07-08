import frappe

from erpnext_china.hrms_china.custom_form_script.employee.employee import get_employee_tree

def has_query_permission(user):
	if frappe.db.get_value('Has Role',{'parent':user,'role':'System Manager'}):
		# 如果角色包含管理员，则看到全量
		conditions = ''
	else:
		# 其他情况则只能看到自己,上级可以看到下级
		users = get_employee_tree(parent=user)
		users.append(user)
		users_str = str(tuple(users)).replace(',)',')')
		conditions = f"(`tabOriginal Leads`.`owner` in {users_str})" 
	return conditions

def has_permission(doc, user, permission_type=None):
	if frappe.db.get_value('Has Role',{'parent':user,'role':['in',['System Manager']]}):
		# 如果角色包含管理员，则看到全量
		return True
	else:
		# 其他情况则只能看到自己,上级可以看到下级
		users = get_employee_tree(parent=user)
		users.append(user)
		
		# 拥有当前原始线索关联的CRM线索的权限的用户也可以看到原始线索
		crm_lead_name = None
		if doc.crm_lead:
			crm_lead = frappe.get_doc("Lead", doc.crm_lead)
			crm_lead_name = crm_lead.lead_owner

		if (doc.owner in users) or user == crm_lead_name:
			return True
		else:
			return False