# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CheckinGroup(Document):
	def before_save(self):
		for tag in self.tags:
			doc = frappe.get_cached_doc("Checkin Tag", tag.tag)
			doc.linked = 1
			doc.save(ignore_permissions=True)
