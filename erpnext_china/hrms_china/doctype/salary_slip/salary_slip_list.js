frappe.listview_settings["Salary Slip"] = {

    onload: function (listview) {
        listview.page.add_inner_button(__("导出"), function () {
            let records = listview.get_checked_items(true);
            var dialog = new frappe.ui.Dialog({
                title: __(`确定导出${records.length}条记录吗？`),
                fields: [
                    { 
                        "fieldname": "file_type",
                        "fieldtype": "Select",
                        "label": "选择类型",
                        "options": "Excel\nCSV",
                        "default": "Excel"
                    },
                ]
            });
    
            dialog.set_primary_action(__("Submit"), function () {
                let values = dialog.get_values();
                open_url_post('/api/method/erpnext_china.hrms_china.doctype.salary_slip.salary_slip.export', {
                    doctype: "",
                    file_type: values.file_type,
                    export_records: '',
                    export_fields: '',
                    export_filters: '',
                    records: records // 这里参数我们仅需传需要导出的name
                  });
                dialog.hide();
            });
            dialog.show();
        });
    }
}

