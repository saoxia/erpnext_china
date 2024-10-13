frappe.listview_settings["Checkin Group"] = {

    onload: function (listview) {
        listview.page.add_inner_button(__("同步到EBC"), function () {
            frappe.warn('注意！！！',
                `确定要将企微考勤信息同步到EBC吗？同步内容包括通讯录、标签、打卡规则，
                同步大约需要2分钟时间，同步完成后请检查规则关联的标签是否正确`,
                () => {
                    frappe.call('erpnext_china.utils.wechat.api.wecom_to_ebc').then(r => {})
                },
                '确认',
                true // Sets dialog as minimizable
            )
        });
    }
}

