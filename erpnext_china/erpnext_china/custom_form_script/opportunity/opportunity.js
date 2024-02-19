frappe.ui.form.on('Opportunity', {
	refresh(frm) {
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