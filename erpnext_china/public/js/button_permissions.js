$(document).on('app_ready', function() {
	if (document.referrer.includes("/login")) {
		frappe.call({
			'method': "erpnext_china.erpnext_china.doctype.button_permission.button_permission.get_button_permission",
			'callback': function(response) {
				if (response.message) {
                    frappe.button_perms = response.message;
				}
			}
		});
	}
});