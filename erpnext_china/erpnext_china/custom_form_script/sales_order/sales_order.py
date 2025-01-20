import frappe
from frappe import _
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
from erpnext.selling.doctype.sales_order.sales_order import make_purchase_order_for_default_supplier
import json
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    set_party_type,
    set_party_account,
    set_party_account_currency,
    set_paid_amount_and_received_amount,
    get_bank_cash_account,
    set_grand_total_and_outstanding_amount,
    set_payment_type
)
import frappe.utils
from erpnext.selling.doctype.sales_order.sales_order import WarehouseRequired
from frappe.utils import cint

class CustomSalesOrder(SalesOrder):

    @frappe.whitelist()
    def get_p13(self):
        company = self.company
        name = frappe.db.get_value('Sales Taxes and Charges Template', filters={'company': company, 'tax_category': 'P13专票含税'}, fieldname='name')
        if name:
            return {'name': name}

    def before_validate(self, method=None):
        items = [d.item_code for d in self.items]
        # 只从数据库读取一次
        default_warehouse_list = frappe.get_all('Item Default', 
                filters={"parent":['in',items], 'default_warehouse':['!=','']},
                fields=['parent as item_code','company','default_warehouse']
            )
        for item in self.items:
            company_warehouse = [d.default_warehouse for d in default_warehouse_list if d.company == self.company and d.item_code==item.item_code]
            if len(company_warehouse) == 0:
                shipping_company = [d.company for d in default_warehouse_list if d.company != self.company and d.item_code==item.item_code]
                if len(shipping_company) > 0:
                    if len(shipping_company) == 1:
                        shipping_company.append('')

                    query = f"""
                        select
                            sup.name
                        from
                            `tabSupplier` sup, `tabAllowed To Transact With` al
                        where
                            sup.name = al.parent
                            and sup.is_internal_supplier = 1
                            and al.parenttype = 'Supplier'
                            and al.company = '{self.company}'
                            and sup.represents_company in {tuple(shipping_company)}
                    """
                    internal_supplier = frappe.db.sql(query,as_dict=1)
                    if not internal_supplier:
                        frappe.throw("行 #{0} 的物料{1}已有默认仓库归属的公司{2}，但是并没有对应的内部供应商，请先创建内部供应商信息".format(item.idx, item.item_code, shipping_company[0]))
                    item.delivered_by_supplier = 1
                    item.supplier = internal_supplier[0].name
                else:
                    frappe.throw("行 #{0} 的物料没有公司{1}的默认值配置，请添加配置或检查是否用错了下单公司".format(item.idx, self.company))
        
        # 此时is_internal_customer字段可能还没被赋值
        internal_customer = frappe.db.exists("Customer", {"name":self.customer,"is_internal_customer": 1, "disabled": 0})
        if internal_customer:
            self.clear_drop_ship()
            self.get_final_customer()

    def set_employee_and_department(self):
        if self.is_new():
            employee = frappe.db.get_value('Employee', {'user_id': frappe.session.user}, ["name", "department"], as_dict=1)
            if employee:
                self.custom_employee = employee.name
                self.custom_department = employee.department
    
    def set_freight(self):
        if self.is_new() and self.custom_original_sales_order:
            custom_freight = frappe.db.get_value('Sales Order', self.custom_original_sales_order, 'custom_freight')
            self.custom_freight = custom_freight

    def set_state_and_city(self):
        if self.is_new() and self.shipping_address_name:
            address = frappe.db.get_value("Address", self.shipping_address_name, ["state", "city"], as_dict=True)
            if address:
                self.custom_state = address.state
                self.custom_city = address.city

    def set_discount_amount_custom_after_distinct__amount_request(self):
        discount_amount = 0
        # process custom_after_distinct__amount_request for internal sales order
        if self.is_internal_customer and self.custom_original_sales_order:
            for item in self.items:
                poi_name = item.purchase_order_item
                soi_name = frappe.db.get_value("Purchase Order Item", poi_name, 'sales_order_item')
                item.custom_after_distinct__amount_request = frappe.db.get_value("Sales Order Item", soi_name, 'custom_after_distinct__amount_request')

        for d in self.get("items"):
            discount_amount = discount_amount + (d.amount - d.custom_after_distinct__amount_request)
        self.discount_amount = discount_amount

    def before_save(self):
        self.set_employee_and_department()
        self.set_freight()
        self.set_state_and_city()
        self.set_discount_amount_custom_after_distinct__amount_request()
    def after_save(self):
        self.set_discount_amount_custom_after_distinct__amount_request()

    def clear_drop_ship(self):
        for d in self.get("items"):
            d.delivered_by_supplier = 0
            d.supplier = None

    def get_final_customer(self):
        reference_po = list(set([d.purchase_order for d in self.items]))
        if len(reference_po) > 0 and reference_po[0]:
            po_name = reference_po[0]
            query = f"""
                select
                    so.customer, so.name
                from
                    (select
                        distinct poi.sales_order
                    from
                        `tabPurchase Order` po, `tabPurchase Order Item` poi
                    where
                        po.name = poi.parent
                        and po.name = '{po_name}') po_so
                left join
                    `tabSales Order` so on so.name = po_so.sales_order
            """

            res = frappe.db.sql(query,as_dict=1)
            if len(res) > 0:
                self.final_customer = res[0].customer
                self.custom_original_sales_order = res[0].name

    def validate(self):
        super().validate()
        self.validate_taxes_and_charges_of_company()
        self.validate_user_can_sell_item()

    def validate_taxes_and_charges_of_company(self):
        if self.company == '临时' and self.taxes_and_charges:
            frappe.throw('临时公司无需设置销项税/费')

    def validate_user_can_sell_item(self):
        if self.is_new():
            current_employee = frappe.db.get_value("Employee", filters={"user_id": frappe.session.user}, fieldname='name')
            leaders = get_employee_all_leaders(current_employee)
            leaders.append(current_employee)
            can_not_sell_items = []
            for item in self.items:
                item_doc = frappe.get_doc("Item", item.item_code)
                # 如果物料没有指定任何开发人，则允许销售
                developer_list = item_doc.item_developer_list_item
                if not developer_list or len(developer_list) == 0 or 'Administrator' in frappe.get_roles(frappe.session.user):
                    continue
                developer_employee_list = [dev.employee for dev in developer_list]
                # 如果员工及上级不在允许销售负责人列表中
                if len(set(leaders) & set(developer_employee_list)) == 0:
                    can_not_sell_items.append(item_doc.item_name)
            
            if len(can_not_sell_items) > 0:
                msg = ', '.join(can_not_sell_items) + ' 不在可销售范围内'
                frappe.throw(msg)
    def validate_warehouse(self):
        super().validate_warehouse()
        delivered_by_supplier = False
        delivered_by_company = False
        for d in self.get("items"):
            if d.delivered_by_supplier:
                delivered_by_supplier = True
            else:
                delivered_by_company = True
            if (
                (
                    frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1
                    or (
                        self.has_product_bundle(d.item_code)
                        and self.product_bundle_has_stock_item(d.item_code)
                    )
                )
                and not d.warehouse
                and not cint(d.delivered_by_supplier)
            ):
                frappe.throw(
                    _("Delivery warehouse required for stock item {0}").format(d.item_code), WarehouseRequired
                )

            if d.stock_qty < 30 and not cint(d.delivered_by_supplier):
                if '箱' in d.uom and d.qty >= 1:
                    return
                else:
                    uom_avilable = frappe.db.exists('UOM Conversion Detail',
                        {
                            'parent': d.item_code,
                            'parenttype': 'Item',
                            'parentfield': 'uoms',
                            'uom':['like',"%箱%"]
                        })
                    if uom_avilable:
                        conversion_factor = frappe.db.get_value('UOM Conversion Detail',uom_avilable,'conversion_factor')
                        if d.stock_qty >= conversion_factor:
                            return
                        else:
                            sample_warehouse = frappe.db.exists('Warehouse',
                                {
                                    'company': self.company,
                                    'for_sample': 1,
                                    'is_group': 0,
                                    'disabled': 0
                                })
                            if sample_warehouse:
                                d.warehouse = sample_warehouse
                                msg ="""<p>第{}行的物料{}被<b>更新到样品仓库{}</b></p>""".format(
                                    frappe.bold(d.idx),
                                    frappe.bold(d.item_code),
                                    frappe.bold(sample_warehouse),
                                )
                                frappe.msgprint(msg,alert=True)
                            else:
                                msg = """
                                    <p>第{}行的物料{}低于销售要求，且<b style="color:red">未找到样品仓库</b></p>
                                    <p>单位:{}</p>
                                    <p>销售数量:{}</p>
                                    <p>库存单位数量:{}{}</p>
                                    <p>请联系管理员检查配置</p>
                                """.format(
                                    frappe.bold(d.idx),
                                    frappe.bold(d.item_code),
                                    frappe.bold(d.uom),
                                    frappe.bold(d.qty),
                                    frappe.bold(d.stock_qty),
                                    frappe.bold(d.stock_uom),
                                )
                                frappe.throw(msg)
                    else:
                        msg = """
                            <p>第{}行的物料{}低于销售要求，且<b style="color:red">没有设置箱的转换系数</b></p>
                            <p>单位:{}</p>
                            <p>销售数量:{}</p>
                            <p>库存单位数量:{}</p>
                            <p>请联系管理员检查配置</p>
                        """.format(
                            frappe.bold(d.idx),
                            frappe.bold(d.item_code),
                            frappe.bold(d.uom),
                            frappe.bold(d.qty),
                            frappe.bold(d.stock_qty),
                        )
                        frappe.throw(msg,title=_('Error'))
        if delivered_by_supplier and delivered_by_company:
            frappe.throw(_("Cannot deliver both by supplier and company in same sales order"))
def get_employee_all_leaders(employee, leaders=None):
    if leaders is None:
        leaders = []
    reports_to = frappe.db.get_value("Employee", filters={"name": employee}, fieldname="reports_to")
    if reports_to:
        leaders.append(reports_to)
        get_employee_all_leaders(reports_to, leaders)
    return leaders

@frappe.whitelist()
def select_payment_entry(**kwargs):
    kwargs.pop('cmd')
    fields = ['name','docstatus'] + list(kwargs.keys())
    if 'reference_date' not in fields:
        fields.append('reference_date')
    custom_payment_note = kwargs.pop('custom_payment_note')
    reference_no = kwargs.pop('reference_no')
    filters = {k:v for k,v in kwargs.items() if v and k not in ('unallocated_amount','include_submitted_doc')}
    
    include_submitted_doc = kwargs.pop('include_submitted_doc')
    if int(include_submitted_doc) == 1:
        filters['docstatus'] = ['<',2]
    else:
        filters['docstatus'] = ['=',0]

    if custom_payment_note:
        filters['custom_payment_note'] = ['like', f'%{custom_payment_note}%']
    if reference_no:
        filters['reference_no'] = ['like', f'%{reference_no}%']
    results = frappe.get_list("Payment Entry", filters=filters, fields=fields)
    return results    

def make_internal_purchase_order(doc,method=None):
    if frappe.db.get_single_value("Selling Settings", "allow_generate_inter_company_transactions"):
        internal_suppliers = frappe.get_all('Supplier', filters={'is_internal_supplier':1,'disabled':0},pluck='name')
        items = [d for d in doc.items if d.delivered_by_supplier and d.supplier in internal_suppliers]
        if not items:
            return
        current_user = frappe.session.user
        frappe.set_user("Administrator")
        purchase_orders = make_purchase_order_for_default_supplier(doc.name, items)
        msg = f"""
            <h5>已自动生成{len(purchase_orders)}张采购订单</h5>
        """
        for po in purchase_orders:
            validate_po_item_price(po,doc)
            po.save()
            po.db_set('owner',doc.owner)
            po.submit()
            msg += f"""
                <a href="/app/purchase-order/{po.name}" target="_blank">{po.name}</a>
            """
        frappe.msgprint(f"""<div>{msg}<div>""",alert=1)
        frappe.set_user(current_user)

def validate_po_item_price(po,so):
    if frappe.get_all('Price List',filters={'buying':1,'selling':1,'currency':so.currency}):
        for d in po.items:
            if d.rate == 0:
                so_rate = [soi.rate for soi in so.items if soi.name == d.sales_order_item][0]
                d.rate = so_rate
        if so.apply_discount_on and so.discount_amount:
            po.apply_discount_on = so.apply_discount_on
            po.discount_amount = so.discount_amount

@frappe.whitelist()
def matching_payment_entries(docname,payment_entries):
    doc = frappe.get_doc('Sales Order',docname)
    if isinstance(payment_entries,str):
        payment_entries = json.loads(payment_entries)
    
    payment_type = set_payment_type(doc.doctype, doc)
    bank = get_bank_cash_account(doc, None)
    party_type = set_party_type(doc.doctype)
    party_account = set_party_account(doc.doctype, doc.name, doc, party_type)
    party_account_currency = set_party_account_currency(doc.doctype, party_account, doc)

    party_amount = None
    bank_amount = None
    grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(
        party_amount, doc.doctype, party_account_currency, doc
    )
    paid_amount, received_amount = set_paid_amount_and_received_amount(
        doc.doctype, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc
    )

    if outstanding_amount == 0:
        frappe.throw(_('{0} {1} has already been fully paid.').format(_('Sales Order'), doc.name))
    # sales order is still draft now, no need to check payment against sales invoices
    unallocated_amount = outstanding_amount
    matched_pe = []

    for pe in payment_entries:
        if unallocated_amount <= 0:
            break
        pe_doc = frappe.get_doc('Payment Entry',pe)
        if pe_doc.docstatus == 1:
            frappe.msgprint(_('Ignored row for {0}').format(pe_doc.name),alert=True)
            continue
        if pe_doc.company != doc.company:
            frappe.msgprint(_('Payment Entry {0} does not belong to company {1}'.format(pe_doc.name,doc.company)),alert=True)
            continue

        
        
        if pe_doc.docstatus == 0:
            
            if pe_doc.paid_amount <= unallocated_amount:
                
                pe_doc.update({
                    'party_type': 'Customer',
                    'party': doc.customer,
                })
                pe_doc.append(
					"references",
					{
						"reference_doctype": doc.doctype,
						"reference_name": doc.name,
						"bill_no": doc.get("bill_no"),
						"due_date": doc.get("due_date"),
						"total_amount": grand_total,
						"outstanding_amount": unallocated_amount,
						"allocated_amount": pe_doc.paid_amount,
					},
				)
                try:
                    pe_doc.save().submit()
                    unallocated_amount -= pe_doc.paid_amount
                    matched_pe.append(pe_doc)
                except Exception as e:
                    frappe.log_error(e)
                    frappe.msgprint(_('Check the Error Log for more information: {0}').format(pe_doc.name),alert=True)
                    continue
            else:
                diff_payment_entry = frappe.copy_doc(pe_doc)
                diff_payment_entry.update({
                    'party':doc.customer,
                    'paid_amount': pe_doc.paid_amount - unallocated_amount,
                })

                pe_doc.update({
                    'party_type': 'Customer',
                    'party': doc.customer,
                    'paid_amount': unallocated_amount,
                    'manual_split':1
                })
                pe_doc.append(
					"references",
					{
						"reference_doctype": doc.doctype,
						"reference_name": doc.name,
						"bill_no": doc.get("bill_no"),
						"due_date": doc.get("due_date"),
						"total_amount": grand_total,
						"outstanding_amount": unallocated_amount,
						"allocated_amount": unallocated_amount,
					},
				)
                try:
                    pe_doc.save().submit()
                    unallocated_amount -= pe_doc.paid_amount
                    matched_pe.append(pe_doc)

                    diff_payment_entry.insert()
                    diff_payment_entry.add_comment("Comment",_('Split From {0} By System').format(pe_doc.name))
                    break
                except Exception as e:
                    frappe.log_error(e)
                    frappe.msgprint(_('Check the Error Log for more information: {0}').format(pe_doc.name),alert=True)
                    continue

    return {
        'matched_pe': matched_pe,
        'unallocated_amount': unallocated_amount
    }