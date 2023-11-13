// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Opportunity', {
	refresh(frm) {
	// 删除【商机来源】下拉选项中的意向客户
	frm.set_query("quotation_to", function() {
		return{
			"filters": {
				"name": ["in", ["Customer", "Lead"]]
			}
		}
	});

	}
})