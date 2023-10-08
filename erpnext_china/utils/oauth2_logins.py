# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import frappe
import frappe.utils
from frappe.utils.oauth import login_oauth_user

@frappe.whitelist(allow_guest=True)
def login_via_wecom(code: str, state: str):
	info = {'email':'lingyu_li@foxmail.com',
		 	'userid':'lingyu_li@foxmail.com',}
	login_oauth_user(info, provider='wecom', state=None)