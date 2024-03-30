# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.utils.password import get_decrypted_password
from erpnext_china.utils.oauth2_logins import get_access_token

class WeComSetting(Document):
	pass




@frappe.whitelist(allow_guest=True)
def update_access_token():
	#client_id = frappe.db.get_single_value('WeCom Setting', 'client_id')
	#client_secret = frappe.db.get_single_value('WeCom Setting', 'client_secret')
	# access_token = get_access_token(client_id,client_secret)
	client_info = frappe.db.get_singles_dict('WeCom Setting')
	access_token = get_access_token(client_info['client_id'],client_info['client_secret'])

	frappe.db.set_single_value('WeCom Setting', 'access_token', access_token)