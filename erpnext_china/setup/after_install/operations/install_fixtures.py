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
	import shutil
	source_path = Path(__file__).parent.parent / 'workspace' / 'buying' / 'buying.json'
	target_path = Path(__file__).parent.parent.parent.parent.parent.parent / 'erpnext' / 'erpnext' / 'buying' / 'workspace'  / 'buying' / 'buying.json'
	shutil.copy2(source_path, target_path)
