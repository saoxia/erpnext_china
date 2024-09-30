frappe.listview_settings["Checkin Group"] = {

    onload: function (listview) {
        listview.page.add_inner_button(__("同步到企微"), function () {
            frappe.warn('警告！！！',
                '确定要将当前考勤规则同步到企微考勤吗？',
                () => {
                    // frappe.call('erpnext_china.utils.timed_tasks.task_update_wecom_staff').then(r => {})
                },
                '确认',
                true // Sets dialog as minimizable
            )
        });
    }
}

