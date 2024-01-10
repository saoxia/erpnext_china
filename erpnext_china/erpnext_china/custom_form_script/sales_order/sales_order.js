// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Sales Order', {
	refresh(frm) {
		// your code here
		frm.fields_dict['items'].grid.get_field('uom').get_query = function(doc, cdt, cdn){
			var row = locals[cdt][cdn];
			return {
				query:"erpnext.accounts.doctype.pricing_rule.pricing_rule.get_item_uoms",
				filters: {'value':row.item_code, apply_on:"Item Code"},
				
			}
	}
	}
})