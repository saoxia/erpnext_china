# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json
import os
from pathlib import Path

import frappe
from frappe import _
from frappe.desk.page.setup_wizard.setup_wizard import make_records


def install(country='China'):
	records = []
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