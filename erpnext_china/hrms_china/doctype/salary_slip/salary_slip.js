// Copyright (c) 2024, Digitwise Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Slip", {
    refresh(frm) {
        const totalAmount = frm.doc.total_amount;
        let fmtTotalAmount = totalAmount ? totalAmount.toFixed(2) : 0;
        const totalRow = document.querySelector('.total-row');
        if (totalRow) {
            const totalNum = totalRow.querySelector('.total-num');
            if (totalNum) {
                totalNum.innerText = fmtTotalAmount;
            }
        } else {
            const totalAmountRowTemplate = `
            <div class="grid-row total-row" style="border-top: 1px solid var(--table-border-color);">
                <div class="data-row row">
                    <div class="row-check sortable-handle col"></div>
                    <div class="row-index sortable-handle col"></div>
                    <div class="col grid-static-col col-xs-7 bold" data-fieldname="component" data-fieldtype="Link">
                        <div class="field-area" style="display: none;"></div>
                        <div class="static-area ellipsis reqd">总计</div>
                    </div>
                    <div class="col grid-static-col col-xs-3  text-right" data-fieldname="amount" data-fieldtype="Currency">
                        <div class="field-area" style="display: none;"></div>
                        <div class="static-area ellipsis">
                            <div class="total-num" style="text-align: right;font-weight: bold;">${fmtTotalAmount}</div>
                        </div>
                    </div>
                    <div class="col"></div>
                </div>
            </div>
        `
            const rows = document.querySelector('.rows');
            const parser = new DOMParser();
            const doc = parser.parseFromString(totalAmountRowTemplate, 'text/html');
            const templateDom = doc.querySelector('.total-row');
            if (rows && templateDom) {
                rows.parentNode.insertBefore(templateDom, rows.nextElementSibling);
            }
        }
    },
});
