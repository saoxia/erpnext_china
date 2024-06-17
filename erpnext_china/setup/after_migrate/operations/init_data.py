import frappe

def init_original_clue_sources():
    clue_sources = {
        "1": '字节-巨量广告',
        "2": '其他渠道-外部导入',
        "5": '字节-抖音企业号',
        "7": '字节-巨量线索',
        "8": '字节-云店',
        "9": '字节-星图',
        "10": '字节-获客宝',
        "11": '字节-住小帮',
    }
    doctype = 'Original Clue Sources'
    existing_ids = [doc.clue_source_id for doc in frappe.get_list(doctype=doctype, fields=['clue_source_id'])]
    records_to_create = [
		{"doctype": doctype, "clue_source_id": k, "clue_source_name": v} 
		for k, v in clue_sources.items() if k not in existing_ids
		]
    for doc_data in records_to_create:
        try:
            doc = frappe.get_doc(doc_data)  
            doc.insert(ignore_permissions=True)
        except:
            pass


def init_orignal_flow_types():
    flow_types = {
        "1": "经营-自然流量线索",
        "2": "经营-广告直接线索",
        "3": "经营-广告间接线索",
        "4": "广告线索",
        "5": "无",
    }
    doctype = 'Original Flow Types'
    existing_ids = [doc.flow_type_id for doc in frappe.get_list(doctype=doctype, fields=['flow_type_id'])]
    records_to_create = [
		{"doctype": doctype, "flow_type_id": k, "flow_type_name": v} 
		for k, v in flow_types.items() if k not in existing_ids
		]
    for doc_data in records_to_create:
        try:
            doc = frappe.get_doc(doc_data)  
            doc.insert(ignore_permissions=True)
        except:
            pass


def init_original_clue_types():
    clue_types = {
        "0": "字节-表单提交",
        "1": "字节-在线咨询",
        "2": "字节-智能电话",
        "3": "字节-网页回呼",
        "4": "字节-卡券",
        "5": "字节-抽奖",
    }
    doctype = 'Original Clue Types'
    existing_ids = [doc.clue_type_id for doc in frappe.get_list(doctype=doctype, fields=['clue_type_id'])]
    records_to_create = [
		{"doctype": doctype, "clue_type_id": k, "clue_type_name": v} 
		for k, v in clue_types.items() if k not in existing_ids
		]
    for doc_data in records_to_create:
        try:
            doc = frappe.get_doc(doc_data)  
            doc.insert(ignore_permissions=True)
        except:
            pass

def init():
    """初始化一些数据"""
    init_original_clue_sources()
    init_orignal_flow_types()
    init_original_clue_types()