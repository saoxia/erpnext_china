# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.xlsxutils import build_xlsx_response
from frappe.core.doctype.data_import.exporter import Exporter

class SalarySlip(Document):
	

	@property
	def total_amount(self):
		total = 0
		for i in self.salary_detail:
			doc = frappe.get_doc('Salary Component', i.component)
			if doc.type == '收入':
				total += i.amount
			else:
				total -= i.amount
		return total


@frappe.whitelist()
def export(doctype, export_fields=None, export_records=None, export_filters=None, file_type="CSV", records=[]):
	if isinstance(records, str):
		records = json.loads(records)
	doctype = "Salary Slip"
	export_fields = {'Salary Slip': ['name', 'employee', 'company', 'employee_name', 'department', 'designation', 'posting_date', 'status', 'payroll_frequency', 'start_date', 'end_date', 'amended_from']}
	export_records = 'by_filter'
	export_filters = [['Salary Slip', 'name', 'in', records]]
	file_type = 'Excel'
	export_data = True

	e = Exporter(
		doctype,
		export_fields=export_fields,
		export_data=export_data,
		export_filters=export_filters,
		file_type=file_type,
		export_page_length=5 if export_records == "5_records" else None,
	)
	export_data = e.get_csv_array_for_export()
	header = export_data[0]
	
	salary_component_names = frappe.db.get_all('Salary Component', pluck='name', order_by="creation")
	header += salary_component_names

	new_datas = [header]
	for data in export_data[1:]:
		name = data[0]
		# [0,0]
		other_data = [0] * len(salary_component_names)
		details = frappe.db.get_all("Salary Detail", filters={"parent": name}, fields=["component", "amount"])
		for detail in details:
			# 奖金 in ["基本工资", "奖金"]
			if detail.component in salary_component_names:
				index = salary_component_names.index(detail.component)
				other_data[index] = detail.amount
		new_datas.append(data+other_data)

	build_xlsx_response(new_datas, _(doctype))