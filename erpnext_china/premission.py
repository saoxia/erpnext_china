import frappe 
def lead_query_conditions(user):
    user = frappe.user
    if frappe.db.get_value('Has Role',{'parent':user,'role':'System Manager'}):
        # 如果角色包含管理员，则看到全量
        conditions = ''
    else:
        # 其他情况则只能看到自己拥有的线索
        # 待添加上级可以看到下级的线索
        conditions = f"owner in ('{user}')" 
    return conditions 