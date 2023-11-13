frappe.ui.form.on('Sales Order', {
	onload(frm) {
		// 删除按钮
		frm.remove_custom_button(__("Prospect"), __('Create'));
		frm.remove_custom_button(__('Add to Prospect'), __('Create'));
		}
	})