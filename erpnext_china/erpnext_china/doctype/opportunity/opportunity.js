frappe.ui.form.on('Opportunity', {
	refresh(frm) {
	// 产出采购相关按钮
	frm.remove_custom_button(__('Supplier Quotation'), __('Create'));
	frm.remove_custom_button(__('Request For Quotation'), __('Create'));
	// 删除【商机来源】下拉选项中的意向客户
	frm.set_query("opportunity_from", function() {
		return{
			"filters": {
				"name": ["in", ["Customer", "Lead"]]
			}
		}
	});

	}
})