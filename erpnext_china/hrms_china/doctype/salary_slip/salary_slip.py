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
def export(doctype, export_fields=None, export_records=None, 
		   export_filters=None, file_type="CSV", records=[]):
	if isinstance(records, str):
		records = json.loads(records)
	doctype = "Salary Slip"
	export_fields = {
		'Salary Slip': [
			'name', 'employee', 'company', 'employee_name', 'department', 'designation', 
			'posting_date', 'status', 'payroll_frequency', 'start_date', 'end_date', 'amended_from'
			],
		'salary_detail': ['component', 'amount']
		}
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
	# ['ID', '员工', '公司', '员工姓名', '部门', '职位', '记帐日期', '状态', '工资发放频率', '开始日期', '结束日期', '修订源', '薪资构成 (薪资详细信息)', '金额 (薪资详细信息)']
	# ['HR-SA-HR-EMP-00531---68084', 'HR-EMP-00531', '山东朱氏药业集团有限公司', None, None, None, None, '草稿', '按月发放', None, None, None, '基本工资', 12.0]
	# ['', '', '', '', '', '', '', '', '', '', '', '', '基本工资', 1000.0]
	# ['', '', '', '', '', '', '', '', '', '', '', '', '奖金', 1000.0]
	export_data = e.get_csv_array_for_export()
	# 去掉'薪资构成 (薪资详细信息)', '金额 (薪资详细信息)'
	header = export_data[0][:-2]
	# 合并表头 ['基本工资','奖金','分红', ...]
	extend_headers = frappe.db.get_all('Salary Component', pluck='name', order_by="creation")
	header += extend_headers

	# 构建合并后的初始数据结构
	final_data = [header]

	# 根据薪资项个数预先构建初始的薪资项数据[0, 0, 0]
	salary_detail_extend = [0] * len(extend_headers)

	only_rows = export_data[1:]
	current_data = []
	for row in only_rows:
		if row[0]:
			if current_data:
				final_data.append(current_data)
			current_data = row[:-2] + salary_detail_extend
		idx = header.index(row[-2])
		current_data[idx] = row[-1]  # 如果数据没有对齐，则需要报错
	final_data.append(current_data)

	build_xlsx_response(final_data, _(doctype))