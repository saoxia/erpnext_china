const PermissionForm = class PermissionForm extends frappe.ui.form.Form {
	add_custom_button(label, fn, group) {		
		// const button_perms = frappe.button_perms;

		
		// 从localStorage中获取存储的字符串
		var storedJsonString = localStorage.getItem('button_perms_jsonString');
		// 将存储的字符串转换回字典
		var button_perms = JSON.parse(storedJsonString) || {};


		if (this.doctype in button_perms) {
			if (!(button_perms[this.doctype]['label_info'].includes((label+'__'+group).replace('undefined','')))) {
				// temp! old parameter used to be icon
				if (group && group.indexOf("fa fa-") !== -1) group = null;

				let btn = this.page.add_inner_button(label, fn, group);

				if (btn) {
					// Add actions as menu item in Mobile View
					let menu_item_label = group ? `${group} > ${label}` : label;
					let menu_item = this.page.add_menu_item(menu_item_label, fn, false);
					menu_item.parent().addClass("hidden-xl");

					this.custom_buttons[label] = btn;
				}
				return btn;
			}
		} 
		else {
			// temp! old parameter used to be icon
			if (group && group.indexOf("fa fa-") !== -1) group = null;
			let btn = this.page.add_inner_button(label, fn, group);

			if (btn) {
				// Add actions as menu item in Mobile View
				let menu_item_label = group ? `${group} > ${label}` : label;
				let menu_item = this.page.add_menu_item(menu_item_label, fn, false);
				menu_item.parent().addClass("hidden-xl");

				this.custom_buttons[label] = btn;
				}
				return btn;
		}
	}
}

frappe.ui.form.Form = PermissionForm
