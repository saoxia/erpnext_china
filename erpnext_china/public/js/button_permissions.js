$(document).on('app_ready', function() {
	if (document.referrer.includes("/login")) {
		frappe.call({
			'method': "erpnext_china.erpnext_china.doctype.button_permission.button_permission.get_button_permission",
			'callback': function(response) {
				if (response.message) {
                    // frappe.button_perms = response.message;
					
					// 要存储的字典
					var button_perms = response.message;
					// 将字典转换为字符串
					var button_perms_jsonString = JSON.stringify(button_perms);
					// 使用localStorage存储字符串
					localStorage.setItem('button_perms_jsonString', jsonString);
				}
			}
		});
	}
});