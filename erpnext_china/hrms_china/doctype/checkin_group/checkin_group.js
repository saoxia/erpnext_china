// Copyright (c) 2024, Digitwise Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Checkin Group", {
	refresh(frm) {
        frm.add_custom_button(__('同步到企微'), () => {
            let d = new frappe.ui.Dialog({
                title: '将此考勤规则同步到企微',
                fields: [
                    {
                        "fieldname": "effective_now",
                        "fieldtype": "Check",
                        "label": "立即生效",
                        "default": false
                    },
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    const effective_now = values['effective_now'];
                    const group_id = frm.doc.name;
                    frappe.call({
                        method: 'erpnext_china.utils.wechat.api.group_write_into_wecom',
                        args: {
                            effective_now,
                            group_id
                        },
                        // disable the button until the request is completed
                        btn: $('.primary-action'),
                        // freeze the screen until the request is completed
                        freeze: true,
                        callback: (r) => {
                            frappe.msgprint({
                                title: __('同步完成'),
                                indicator: 'green',
                                message: __('请前往企微检查考勤打卡规则！')
                            });
                        },
                        error: (e) => {
                            frappe.msgprint({
                                title: __('同步失败'),
                                indicator: 'red',
                                message: __(e.message)
                            })
                        }
                    })
                    
                    d.hide();
                }
            });
            d.show();
        });
        frm.add_custom_button(__('删除对应的企微规则'), () => {
            let d = new frappe.ui.Dialog({
                title: '确定要删除对应的API创建的企微规则吗？',
                size: 'small',
                primary_action_label: 'Submit',
                primary_action(values) {
                    const group_id = frm.doc.name;
                    frappe.call({
                        method: 'erpnext_china.utils.wechat.api.delete_group',
                        args: {
                            group_id
                        },
                        btn: $('.primary-action'),
                        freeze: true,
                        callback: (r) => {
                            frappe.msgprint({
                                title: __('删除完成'),
                                indicator: 'green',
                                message: __('请前往企微检查考勤打卡规则！')
                            });
                        },
                        error: (e) => {
                            frappe.msgprint({
                                title: __('删除失败'),
                                indicator: 'red',
                                message: __(e.message)
                            })
                        }
                    })
                    
                    d.hide();
                }
            });
            d.show();
        });
    },
});
