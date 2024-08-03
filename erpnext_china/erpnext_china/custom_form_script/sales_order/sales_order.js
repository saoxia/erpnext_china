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
	}
})


frappe.ui.form.on("Sales Order Item", {
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
        row.warehouse = ''
		if (frm.doc.delivery_date) {
			row.delivery_date = frm.doc.delivery_date;
			refresh_field("delivery_date", cdn, "items");
		} else {
			frm.script_manager.copy_from_first_row("items", row, ["delivery_date"]);
		}
        frappe.call("erpnext_china_mdm.mdm.custom_form_script.item.get_item_default_warehouse", {item_code: row.item_code, company: frm.doc.company}).then((r)=>{
            if(r.message) {
                row.warehouse = r.message;
                refresh_field("warehouse", cdn, "items");
            }
        })
	},
	delivery_date: function (frm, cdt, cdn) {
		if (!frm.doc.delivery_date) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "items", "delivery_date");
		}
	}
});