# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json
import os
from pathlib import Path

import frappe
from frappe import _
from frappe.desk.page.setup_wizard.setup_wizard import make_records


def install(country='China'):
	records = [
		# territory: with two default territories, one for home country and one named Rest of the World
		{
			"doctype": "Territory",
			"territory_name": _("All Territories"),
			"is_group": 1,
			"name": _("All Territories"),
			"parent_territory": "",
		}
	]
	#中国行政区划
	import csv
	with open((Path(__file__).parent.parent / "data" / 'territory.csv'), mode='rt',encoding="utf-8-sig") as file:
		reader = csv.DictReader(file)
		for line in reader:
			territory_ = {
				"doctype": "Territory",
				"territory_name": _(line['区域名称']),
				"is_group": int(line['是否群组']),
				"parent_territory": _(line['上级区域']),
				}
			records.append(territory_)

	make_records(records)

	overwrite_workspace()

#修改workspace文件
def overwrite_workspace():
	#直接在源文件上修改
	workspace_file_path =[(Path(__file__).parent.parent.parent.parent.parent.parent / 'frappe' / 'frappe' / 'automation' / 'workspace'  / 'tools' / 'tools.json')
					   	,(Path(__file__).parent.parent.parent.parent.parent.parent / 'frappe' / 'frappe' / 'website' / 'workspace'  / 'website' / 'website.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'frappe' / 'frappe' / 'core' / 'workspace'  / 'build' / 'build.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'frappe' / 'frappe' / 'integrations' / 'workspace'  / 'integrations' / 'integrations.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'setup' / 'workspace'  / 'home' / 'home.json')
					    ,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'accounts' / 'workspace'  / 'accounting' / 'accounting.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'assets' / 'workspace'  / 'assets' / 'assets.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'quality_management' / 'workspace'  / 'quality' / 'quality.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'projects' / 'workspace'  / 'projects' / 'projects.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'support' / 'workspace'  / 'support' / 'support.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'setup' / 'workspace'  / 'erpnext_settings' / 'erpnext_settings.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'erpnext_integrations' / 'workspace'  / 'erpnext_integrations' / 'erpnext_integrations.json')
						,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'crm' / 'workspace' / 'crm' / 'crm.json')
   		 				,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'buying' / 'workspace' / 'buying' / 'buying.json')
   		 				,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'manufacturing' / 'workspace' / 'manufacturing' / 'manufacturing.json')
   		 				,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'selling' / 'workspace' / 'selling' / 'selling.json')
   		 				,(Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'stock' / 'workspace' / 'stock' / 'stock.json')
						 ]
	for i in workspace_file_path:
		save_workspace_blocks(i)

def save_workspace_blocks(file_path):
	import warnings,json
	with open(file_path, 'r') as file:
		file_content = file.read()

	# 替换英文的单词
	updated_content = file_content \
		.replace('<b>Your Shortcuts</b>', '<b>快捷入口</b>') \
		.replace('<b>Reports &amp; Masters</b>', '<b>功能&报表</b>') \
		.replace('<b>Quick Access</b>', '<b>快捷入口</b>')

	#使修改后的workspace生效
	data = json.loads(updated_content)
	args = {
			"title": data['title'],
			"public": data['public'],
			"new_widgets": json.dumps({}),
			"blocks": data['content']
		}
	
	try:
		frappe.call("frappe.desk.doctype.workspace.workspace.save_page", **args)
	except frappe.exceptions.LinkValidationError as e:
		# 捕获 LinkValidationError 错误并将其转换为警告
		warning_message = str(e)  # 将异常消息转换为字符串
		warnings.warn(warning_message, Warning)