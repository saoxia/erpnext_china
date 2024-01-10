frappe.ui.form.on('Sales Order', {
	onload(frm) {
		// 销售订单选择物料时，只选择已经定义的UOM
		frm.fields_dict['items'].grid.get_field('uom').get_query = function(doc, cdt, cdn){
			var row = locals[cdt][cdn];
			return {
				query:"erpnext.accounts.doctype.pricing_rule.pricing_rule.get_item_uoms",
				filters: {'value':row.item_code, apply_on:"Item Code"},
			}
		};
	}})
