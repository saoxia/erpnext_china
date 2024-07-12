// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
// Script for ToDo Form
frappe.ui.form.on('Lead', {
    // on refresh event
    refresh(frm) {
        // if reference_type and reference_name are set,
        // add a custom button to go to the reference form

        if (!frm.is_new()) {
            if(frappe.session.user == frm.doc.lead_owner) {
                frm.add_custom_button(__("放弃线索"), ()=>{
                    // frappe.db.set_value('Lead', frm.doc.name, {lead_owner: null});
                    frappe.call("erpnext_china.erpnext_china.custom_form_script.lead.lead.give_up_lead", {lead: frm.doc.name}).then((r)=>{
                        console.log(r);
                        window.location.reload();
                    })
                }, __("Action"));
            } else {
                if(frm.doc.lead_owner == "" || frm.doc.custom_sea == "公海") {
                    frm.add_custom_button(__("认领线索"), ()=>{
                        // frappe.db.set_value('Lead', frm.doc.name, {lead_owner: frappe.session.user});
                        frappe.call("erpnext_china.erpnext_china.custom_form_script.lead.lead.get_lead", {lead: frm.doc.name}).then((r)=>{
                            console.log(r);
                            window.location.reload();
                        })
                        
                    }, __("Action"));
                }
            }
        }
    }
})