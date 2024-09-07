// Copyright (c) 2024, Digitwise Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("WeCom Message", {
	refresh(frm) {
        if (!frm.doc.lead) {
            frm.add_custom_button(__('创建线索'), () => {
                let d = new frappe.ui.Dialog({
                    title: '选择原始线索创建CRM线索',
                    fields: [
                        {
                            "fieldname": "original_lead",
                            "fieldtype": "Link",
                            "label": "Original Lead",
                            "options": "Original Leads",
                            "reqd": 1,
                            "link_filters": "[[\"Original Leads\",\"crm_lead\",\"=\",\"\"],[\"Original Leads\",\"solution_type\",\"=\",\"wechat\"]]",
                        },
                    ],
                    size: 'small', // small, large, extra-large 
                    primary_action_label: 'Submit',
                    primary_action(values) {
                        const original_lead = values['original_lead']
                        const message = frm.doc.name
                        console.log(original_lead, message)
                        if (original_lead && message) {
                            frappe.call({
                                method: 'erpnext_china.utils.wechat.api.msg_create_lead_handler',
                                args: {
                                    original_lead,
                                    message
                                },
                                // disable the button until the request is completed
                                btn: $('.primary-action'),
                                // freeze the screen until the request is completed
                                freeze: true,
                                callback: (r) => {
                                    frappe.msgprint({
                                        title: __('创建成功'),
                                        indicator: 'green',
                                    });
                                    window.location.reload();
                                },
                                error: (e) => {
                                    frappe.msgprint({
                                        title: __('创建失败'),
                                        indicator: 'red',
                                        message: __(e.message)
                                    })
                                }
                            })
                        }
                        d.hide();
                    }
                });
                d.show();
            });
        }
    }
});
