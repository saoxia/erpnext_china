# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CheckinGroup(Document):
	def before_save(self):
		old = self.get_doc_before_save()
		if old:
			old_tags = old.tags
		else:
			old_tags = []
		# 原本有现在没有了
		will_delete = set(old_tags) - set(self.tags)
		for tag in will_delete:
			doc = frappe.get_cached_doc("Checkin Tag", tag.tag)
			doc.linked = 0
			doc.save(ignore_permissions=True)
		# 原本没有，现在有了
		will_add = set(self.tags) - set(old_tags)
		for tag in will_add:
			doc = frappe.get_cached_doc("Checkin Tag", tag.tag)
			doc.linked = 1
			doc.save(ignore_permissions=True)
