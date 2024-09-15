# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

import frappe
import json
from datetime import datetime
from frappe.model.document import Document


class AutoAllocationTimeRule(Document):

	def before_save(self):
		self.clean_by_time_type()
		self.check_date_range()
		self.set_week_string()
		self.set_time_sting()

	def check_date_range(self):
		fmt = r"%Y-%m-%d"
		if self.start_day and self.end_day: 
			start_date = datetime.strptime(self.start_day, fmt).date()
			end_date = datetime.strptime(self.end_day, fmt).date()
			if  start_date > end_date:
				frappe.throw("日期格式错误！")
			
	def clean_by_time_type(self):
		if self.time_rule_type == "Week":
			if len(self.get_week_index()) == 0:
				frappe.throw("请选择至少一个星期日！")
			self.start_day = ''
			self.end_day = ''
		else:
			if not self.start_day or not self.end_day:
				frappe.throw("日期必填！")
			days_of_week = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
			for k in days_of_week:
				setattr(self, k, False)

	def get_week_index(self):
		days_of_week = {
			'monday': 0,
			'tuesday': 1,
			'wednesday': 2,
			'thursday': 3,
			'friday': 4,
			'saturday': 5,
			'sunday': 6
		}
		weeks = [days_of_week[day] for day in days_of_week if getattr(self, day, False)]
		return weeks

	def set_week_string(self):
		weeks = self.get_week_index()
		self.week_string = json.dumps(weeks)
	
	def set_time_sting(self):
		days = {
			0: '一',
			1: '二',
			2: '三',
			3: '四',
			4: '五',
			5: '六',
			6: '天',
		}
		time_str = ', '.join([i.start_time+"—"+i.end_time for i in self.items])
		if self.start_day and self.end_day:
			day_str = f'{self.start_day}—{self.end_day}'
			html_string = f"""<h3>{self.title}:</h3><p>日期: {day_str}</p><p>时间段: {time_str}</p>"""
		else:
			week_str = ', '.join(days[i] for i in json.loads(self.week_string))
			html_string = f"""<h3>{self.title}:</h3><p>星期: {week_str}</p><p>时间段: {time_str}</p>"""
		self.time_string = html_string
		