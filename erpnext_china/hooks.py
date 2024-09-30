app_name = "erpnext_china"
app_title = "ERPNext China"
app_publisher = "Digitwise Ltd."
app_description = "ERPNext中国本地化"
app_email = "lingyu_li@foxmail.com"
app_license = "mit"
app_logo_url = "/assets/erpnext/images/erpnext-logo.svg"
# required_apps = []
add_to_apps_screen = [
	{
		"name": "erpnext_china",
		"logo": "/assets/erpnext/images/erpnext-logo-blue.png",
		"title": "ERPNext China",
		"route": "/app",
		# "has_permission": "erpnext.api.permission.has_app_permission"
	}
]

after_install = "erpnext_china.setup.after_install.operations.install_fixtures.install"

app_include_js = ["erpnext_china.bundle.js"]
app_include_css = "business.bundle.css"

scheduler_events = {
	"cron": {
		"0/3 * * * *": [
			"erpnext_china.hrms_china.doctype.wecom_setting.wecom_setting.update_access_token",
		],
        "*/5 * * * *": [
			"erpnext_china.utils.timed_tasks.task_get_check_in_data",
		],
        "0 0 * * *": [
			"erpnext_china.utils.timed_tasks.task_check_user_in_wecom",
		],
        "*/30 * * * *": [
			"erpnext_china.utils.timed_tasks.task_update_wecom_staff",
		],
	},
}

override_whitelisted_methods = {
	# Legacy (& Consistency) OAuth2 APIs
	#"frappe.www.login.login_via_wecom": "frappe.integrations.oauth2_logins.login_via_wecom",
    "frappe.core.doctype.user.user.switch_theme": "erpnext_china.erpnext_china.overrides.user.user.switch_theme"
}

override_doctype_class = {
    'Social Login Key':'erpnext_china.hrms_china.custom_form_script.social_login_key.social_login_key.SocialLoginKey',
	'Employee':'erpnext_china.hrms_china.custom_form_script.employee.employee.CustomEmployee',
	'Lead':'erpnext_china.erpnext_china.custom_form_script.lead.lead.CustomLead',
}

doctype_js = {
    'Opportunity':'erpnext_china/custom_form_script/opportunity/opportunity.js',
    'Quotation':'erpnext_china/custom_form_script/quotation/quotation.js',
    'Sales Order':'erpnext_china/custom_form_script/sales_order/sales_order.js',
    'Stock Entry':'erpnext_china/custom_form_script/stock_entry/stock_entry.js',
    'Lead': 'erpnext_china/custom_form_script/lead/lead.js'
}
permission_query_conditions = {
    "Original Leads": "erpnext_china.erpnext_china.custom_permission.original_lead.permission_original_lead.has_query_permission",
    # "Contact": "erpnext_china.erpnext_china.custom_permission.contact.permission_contact.has_query_permission",
}

has_permission = {
    "Original Leads": "erpnext_china.erpnext_china.custom_permission.original_lead.permission_original_lead.has_permission",
    # "Contact": "erpnext_china.erpnext_china.custom_permission.contact.permission_contact.has_permission",
}

# doc_events = {
#     "Lead": {
#         "before_save": "erpnext_china.erpnext_china.doctype.auto_allocation_rule.auto_allocation_rule.lead_before_save_handle"
#     }
# }