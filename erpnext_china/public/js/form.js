const MyForm = class MyForm extends frappe.ui.form.Form {
	add_custom_button(label, fn, group) {
		console.log('------------')
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

frappe.ui.form.Form = MyForm