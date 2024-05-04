app_name = "erpnext_china"
app_title = "ERPNext China"
app_publisher = "Digitwise Ltd."
app_description = "ERPNext中国本地化"
app_email = "lingyu_li@foxmail.com"
app_license = "mit"
app_logo_url = "/assets/erpnext/images/erpnext-logo.svg"
# required_apps = []


after_install = "erpnext_china.setup.after_install.operations.install_fixtures.install"


app_include_js = ["erpnext_china.bundle.js"]
app_include_css = "business.bundle.css"

website_route_rules = [
	{"from_route": "/query-report/Stock Ledger", "to_route": "/query-report/Stock Ledger China"},
]

scheduler_events = {
	"cron": {
		"0/3 * * * *": [
			"erpnext_china.hrms_china.doctype.wecom_setting.wecom_setting.update_access_token",
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
}

doctype_js = {
    'Opportunity':'erpnext_china/custom_form_script/opportunity/opportunity.js',
    'Quotation':'erpnext_china/custom_form_script/quotation/quotation.js',
    'Sales Order':'erpnext_china/custom_form_script/sales_order/sales_order.js',
    'Stock Entry':'erpnext_china/custom_form_script/stock_entry/stock_entry.js',
}
permission_query_conditions = {
}

has_permission = {
}