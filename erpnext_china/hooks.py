app_name = "erpnext_china"
app_title = "ERPNext China"
app_publisher = "Digitwise Ltd."
app_description = "ERPNext中国本地化"
app_email = "lingyu_li@foxmail.com"
app_license = "mit"
app_logo_url = "/assets/erpnext/images/erpnext-logo.svg"
# required_apps = []


after_install = "erpnext_china.setup.after_install.operations.install_fixtures.install"

override_whitelisted_methods = {
	# Legacy (& Consistency) OAuth2 APIs
	#"frappe.www.login.login_via_wecom": "frappe.integrations.oauth2_logins.login_via_wecom",
}

override_doctype_class = {
    'Social Login Key':'erpnext_china.erpnext_china.custom_form_script.social_login_key.social_login_key.SocialLoginKey',
	'Employee':'erpnext_china.erpnext_china.custom_form_script.employee.employee.CustomEmployee',
}

doctype_js = {
    'Lead':'erpnext_china/custom_form_script/lead/lead.js',
    'Opportunity':'erpnext_china/custom_form_script/opportunity/opportunity.js',
    'Quotation':'erpnext_china/custom_form_script/quotation/quotation.js',
}
permission_query_conditions = {
    "Lead": "erpnext_china.erpnext_china.custom_form_script.lead.permission_lead.lead_has_query_permission",
    "Quotation": "erpnext_china.erpnext_china.custom_form_script.quotation.permission_quotation.quotation_has_query_permission",
    "Opportunity": "erpnext_china.erpnext_china.custom_form_script.opportunity.permission_opportunity.opportunity_has_query_permission", 
}