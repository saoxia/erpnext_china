# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


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
        print(total)
        return total
