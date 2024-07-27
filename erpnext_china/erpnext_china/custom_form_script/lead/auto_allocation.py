
import frappe

def lead_before_save_handle(doc):

	if not created_lead_by_sale(doc):
		old_doc = doc.get_doc_before_save()
		auto_allocation = doc.custom_auto_allocation
		lead_owner_employee = doc.custom_lead_owner_employee
		
		# 保存前有线索负责员工，说明是手动录入或修改
		if lead_owner_employee:
			if doc.has_value_changed("custom_lead_owner_employee"):
				if not check_lead_total_limit(lead_owner_employee):
					frappe.throw("当前线索负责人客保数量已满，请选择其他负责人！")
				else:
					to_private(doc)
		else:
			if auto_allocation:
				auto_allocate(doc)
			else:
				if old_doc:
					to_public(doc)
				else:
					lead_to_owner_or_public(doc)

def auto_allocate(doc):
	"""自动分配
	找到已启用的规则下的员工 A = []

		如果没有任何启用，则分配给线索创建人，创建人客保数量满，分配到公海
	
	根据A找到符合产品分类和来源的员工 B = []

		如果没有符合条件的员工，则分配给线索创建人，创建人客保数量满，分配到公海
	
	根据B找到客保数量未分配满的员工 C = []

		如果没有可分配员工，分配给线索创建人，创建人客保数量满，分配到公海
	
	根据C找到本轮次未分配满的员工 D = []

		如果D全部分配满，则重置B中所有已分配数量为0，此时C中所有可以分配
	
	取C中最早分配的那个员工进行分配
	"""
	items = get_items_from_rules()
	if len(items) == 0:
		frappe.msgprint("当前分配规则下没有可分配员工！将自动分配给创建员工")
		lead_to_owner_or_public(doc)
	else:
		items = sorted(items, key=lambda x: frappe.utils.get_datetime(x.zero_datetime))
		items = get_items_from_filters(doc.custom_product_category, doc.source, items)
		if len(items) == 0:
			frappe.msgprint(f"产品类别：{doc.custom_product_category}，源：{doc.source} 没有可分配员工！将自动分配给创建员工")
			lead_to_owner_or_public(doc)
		else:
			# 先判断客保数量
			can_allocate_items = get_items_from_total_limit(items)
			if len(can_allocate_items) == 0:
				frappe.msgprint(f"客保数量已达到限制，将自动分配给创建员工")
				lead_to_owner_or_public(doc)
			else:
				# 如果有可以分配的，判断本轮次是否可以分配
				final_items = get_items_from_allocation_limit(can_allocate_items)
				if len(final_items) == 0:
					# 如果本轮次已经分配满了重置
					final_items = reset_allocated_count(can_allocate_items)
				lead_to_employee(doc, final_items[0])

def get_items_from_rules():
	"""
	找到所有启用的规则下的员工
	"""
	rules = frappe.get_all("Auto Allocation Rule", filters={"active": True})
	items = []
	for name in rules:
		rule = frappe.get_doc("Auto Allocation Rule", name)
		items.extend(rule.employee)
	return items

def get_items_from_filters(product_category, source, items):
	"""
	查找符合产品分类和来源的员工

	:param product_category: 当前线索的产品类别
	:param source: 当前线索的来源
	:param items: 子表列表
	"""
	results = []
	for item in items:
		if item.product_category and item.product_category != product_category:
			continue
		if item.lead_source and item.lead_source != source:
			continue
		employee = frappe.db.get_value("Employee", item.employee, ["name", "user_id", "status"], as_dict=True)
		if not employee or not employee.user_id or employee.status != "Active":
			continue
		results.append(item)
	return results

def get_items_from_allocation_limit(items):
	"""
	查找本轮次可分配员工
	"""
	results  = []
	for item in items:
		if check_allocated_limit(item.count, item.allocated_count):
			results.append(item)
	return results

def get_items_from_total_limit(items):
	"""
	查找客保数量未到限制的员工
	"""
	results = []
	for item in items:
		if check_lead_total_limit(item.employee):
			results.append(item)
	return results

def check_allocated_limit(count:int, allocated_count: int)->bool:
	"""
	判断本轮次是否已经分配满额

	:param: count: 配额
	:param: allocated_count: 已分配数量
	"""
	if count > allocated_count:
		return True
	return False

def check_lead_total_limit(employee: str) -> bool:
	"""
	判断客保数量是否已经达到限制

	:param employee: 线索负责员工

	"""
	custom_lead_total = frappe.db.get_value("Employee", employee, fieldname="custom_lead_total") or 0
	count = frappe.db.count("Lead", {
		"custom_lead_owner_employee": employee,
		"status": ["!=", "Converted"]
	})
	if count >= custom_lead_total:
		return False
	return True

def reset_allocated_count(employees):
	"""
	重置本轮次已分配数量
	"""
	for employee in employees:
		employee.allocated_count = 0
		employee.save(ignore_permissions=True)
	return employees


def allocate_lead_to_owner(doc)->bool:
	"""
	将线索分配给线索创建员工
	"""
	user = doc.owner
	employee = frappe.db.get_value("Employee", filters={"user_id": user}, fieldname="name")
	if not employee:
		frappe.msgprint("当前线索创建人没有员工信息！")
		return False
	if check_lead_total_limit(employee):
		doc.custom_lead_owner_employee = employee
		doc.lead_owner = user
		to_private(doc)
		return True
	return False

def lead_to_owner_or_public(doc):
	"""
	分配给创建员工，创建员工客保数量满，进公海
	"""
	if not allocate_lead_to_owner(doc):
		frappe.msgprint("当前线索创建员工客保数量已到限制，自动进入公海！")
		to_public(doc)

def to_public(doc):
	"""
	线索进公海
	"""
	doc.custom_sea = "公海"
	doc.custom_auto_allocation = False
	doc.custom_lead_owner_employee = ''
	doc.lead_owner = ''

def to_private(doc):
	"""
	线索进私海
	"""
	if not doc.custom_lead_owner_employee:
		frappe.throw("未指定线索负责员工，禁止进入私海!")
	old_doc = doc.get_doc_before_save()
	if not old_doc:
		doc.status = "Open"
	doc.custom_sea = "私海"
	doc.custom_auto_allocation = False

def set_latest_note(doc):
	"""
	设置最近反馈
	"""
	if doc.notes and len(doc.notes) > 0:
		notes = sorted(doc.notes, key=lambda x: frappe.utils.get_datetime(x.added_on), reverse=True)
		latest_note = notes[0]
		if latest_note.note and '有新的原始线索' not in str(latest_note.note):
			doc.custom_latest_note_created_time = latest_note.added_on
			doc.custom_latest_note = latest_note.note
			if doc.status == 'Open':
				doc.status = "Lead"

def set_last_lead_owner(doc):
	"""
	设置上一次线索负责人
	"""
	old_doc = doc.get_doc_before_save()
	if old_doc:
		doc.custom_last_lead_owner = old_doc.lead_owner
	else:
		doc.custom_last_lead_owner = ''

def lead_to_employee(doc, item):
	"""
	分配给员工，进入私海
	"""
	employee = frappe.get_doc("Employee", item.employee)
	doc.custom_lead_owner_employee = item.employee
	doc.lead_owner = employee.user_id
	item.allocated_count = item.allocated_count + 1
	item.zero_datetime = frappe.utils.now_datetime()
	item.save(ignore_permissions=True)
	to_private(doc)

def created_lead_by_sale(doc):
	"""
	销售创建线索分配给自己
	"""
	sale_role = len(frappe.get_all('Has Role', {'parent': frappe.session.user,'role': ['in', ['销售']]})) > 0
	admin_role = len(frappe.get_all('Has Role', {'parent': frappe.session.user,'role': ['in', ['System Manager']]})) > 0
	old_doc = doc.get_doc_before_save()
	if sale_role and not admin_role:
		if not old_doc:
			if not allocate_lead_to_owner(doc):
				frappe.msgprint("已经达到客保数量限制，当前线索自动进入公海！")
				to_public(doc)
			return True
	return False