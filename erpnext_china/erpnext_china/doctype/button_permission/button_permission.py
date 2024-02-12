# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe.modules.import_file import get_file_path, read_doc_from_file
import pandas as pd
from frappe.permissions import get_roles

class ButtonPermission(Document):
	pass



@frappe.whitelist()
def get_standard_permissions(doctype):
	meta = frappe.get_meta(doctype)
	if meta.custom:
		doc = frappe.get_doc("DocType", doctype)
		return [p.as_dict() for p in doc.permissions]
	else:
		# also used to setup permissions via patch
		path = get_file_path(meta.module, "DocType", doctype)
		return read_doc_from_file(path).get("permissions")

@frappe.whitelist()
def get_button_permission(doctype,label):
	# 获取当前按钮所限制的权限





	base_role = {'role' : '',
		'permlevel' : 0,
		'read' : 0,
		'write' : 0,
		'create' : 0,
		'select' : 0,
		'delete' : 0,
		'print' : 0,
		'email' : 0,
		'report' : 0,
		'import' : 0,
		'export' : 0,
		'share' : 0,
		'amend' : 0,
		'cancel' : 0,
		'submit' : 0}
	cols = ['read','write','create','select','delete','print','email','report','import','export','share','amend','cancel','submit']
	# 获取doctype配置了权限的角色及具体权限
	df = pd.DataFrame(get_standard_permissions(doctype))
	df.permlevel = df.permlevel.fillna(0) # level值为nan的填充为0
	# 获取当前用户的角色列表
	roles = get_roles(frappe.session.user)
	df = df[df.role.isin(roles)] # 筛选出用户具备的角色和权限
	df_group = df.groupby('permlevel').sum() # 汇总为level级的权限
	df_group = (df_group[cols]>0)*1
	
	

	return 'iaa'
