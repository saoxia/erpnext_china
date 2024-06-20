# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
import copy
import json
from erpnext_china.utils import lead_tools
import frappe
from frappe.model.document import Document
from frappe.utils import datetime, response

class LeaddomainforDouyin(Document):
	pass

def get_clue_source_str(clue_source_id: str):
    clue_sources = {
        "0": '字节-巨量广告',
        "1": '字节-巨量广告',
        "2": '其他渠道-外部导入',
        "5": '字节-抖音企业号',
        "7": '字节-巨量线索',
        "8": '字节-云店',
        "9": '字节-星图',
        "10": '字节-获客宝',
        "11": '字节-住小帮',
    }
    return clue_sources.get(clue_source_id, '未知')

def get_flow_type_str(flow_type_id: str):
    flow_types = {
        "1": "经营-自然流量线索",
        "2": "经营-广告直接线索",
        "3": "经营-广告间接线索",
        "4": "广告线索",
        "5": "无",
    }
    return flow_types.get(flow_type_id, '未知')

def get_clue_type_str(clue_type_id: str):
    clue_types = {
        "0": "字节-表单提交",
        "1": "字节-在线咨询",
        "2": "字节-智能电话",
        "3": "字节-网页回呼",
        "4": "字节-卡券",
        "5": "字节-抽奖",
    }
    return clue_types.get(clue_type_id, '未知')

def split_location(location: str):
    """省+市

    reutrn: (省,市)
    """
    if not location:
        return "", ""
    if "+" not in location:
        return location, location
    province_city = location.split('+')
    return tuple(province_city)

@frappe.whitelist(allow_guest=True)
def lead_via_douyin(**kwargs):

    clue_id = kwargs.get('id')
    if not clue_id:
        frappe.local.response['http_status_code'] = 400
        frappe.local.response.update({'code': 400, 'message': 'Must have id!'})
    try:
        record = lead_tools.get_doc_or_none('Original Leads', {'clue_id': clue_id})
        # 如果数据不存在则直接进行插入
        if not record:
            username = lead_tools.get_username_in_form_detail(kwargs, 'douyin')
            
            # 山东+济南
            location = split_location(kwargs.get('location'))
            clue_source_name = get_clue_source_str(str(kwargs.get('clue_source', '')))
            flow_type_name = get_flow_type_str(str(kwargs.get('flow_type', '')))
            clue_type_name = get_clue_type_str(str(kwargs.get('clue_type', '')))

            kwargs.update(
                {
                    'doctype': 'Original Leads', 
                    'source': 'Douyin',
                    'original_json_data': copy.deepcopy(kwargs),
                    'clue_id': clue_id,
                    'lead_name': username,
                    'clue_phone_number': kwargs.get('telphone'),
                    'wechat_account': kwargs.get('weixin'),
                    'area': kwargs.get('city_name') or location[1],
                    'area_province': kwargs.get('province_name') or location[0],
                    'commit_time': datetime.datetime.fromtimestamp(float(kwargs.get('create_time'))),
                    'site_url': kwargs.get('external_url'),
                    'gender': kwargs.get('gender'),
                    'clue_source': clue_source_name,
                    'flow_type': flow_type_name,
                    'clue_type': clue_type_name,
                    'created_datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            original_lead_doc = frappe.get_doc(kwargs).insert(ignore_permissions=True)
            # 同时生成一条CRM数据
            clue_source_name = lead_tools.get_or_insert_flow_channel_name(clue_source_name, '字节')
            crm_lead_doc = lead_tools.get_or_insert_crm_lead(
                username, 
                clue_source_name, 
                kwargs.get('telphone'),
                kwargs.get('telphone'), 
                kwargs.get('weixin'), 
                kwargs.get('city_name') or location[1], 
                kwargs.get('province_name')  or location[0])
            
            # 添加crm 线索和原始线索之间的关系
            if crm_lead_doc:
                original_lead_doc.crm_lead = crm_lead_doc.name
                original_lead_doc.save()
        frappe.local.response['http_status_code'] = 200
        frappe.local.response.update({"code": 0, "message": "success"})
    except Exception as e:
        # 如果出现异常，回滚之前的操作
        frappe.db.rollback()
        raise e
