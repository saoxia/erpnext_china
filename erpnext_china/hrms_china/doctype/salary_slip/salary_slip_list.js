frappe.listview_settings["Salary Slip"] = {

    onload: function (listview) {
        listview.page.add_inner_button(__("导出"), function () {
            let records = listview.get_checked_items(true);
            open_url_post('/api/method/erpnext_china.hrms_china.doctype.salary_slip.salary_slip.export', {
                doctype: "",
                file_type: '',
                export_records: '',
                export_fields: '',
                export_filters: '',
                records: records // 这里参数我们仅需传需要导出的name
              });
        });
    }
}

