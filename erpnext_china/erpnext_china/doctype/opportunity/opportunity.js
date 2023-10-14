frappe.ui.form.on('Opportunity', {
	refresh(frm) {
	frm.remove_custom_button(__('Supplier Quotation'), __('Create'));
	frm.remove_custom_button(__('Request For Quotation'), __('Create'));
	}
})