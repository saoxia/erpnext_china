frappe.listview_settings["Checkin Group"] = {

    onload: function (listview) {
        listview.page.add_inner_button(__("同步到EBC"), function () {
            frappe.warn('注意！！！',
                `确定要将企微考勤信息同步到EBC吗？同步内容包括通讯录、标签、打卡规则，
                同步大约需要2分钟时间，同步完成后请检查规则关联的标签是否正确`,
                () => {
                    frappe.call('erpnext_china.utils.wechat.api.update_wecom_staff').then(r => {})
                },
                '确认',
                true // Sets dialog as minimizable
            )
        });
        // listview.page.add_inner_button(__("同步到企微"), function () {
        //     frappe.warn('警告！！！',
        //         '确定要将当前考勤规则同步到企微考勤吗？',
        //         () => {
        //             // frappe.call('erpnext_china.utils.timed_tasks.task_update_wecom_staff').then(r => {})
        //         },
        //         '确认',
        //         true // Sets dialog as minimizable
        //     )
        // });
    }
}

