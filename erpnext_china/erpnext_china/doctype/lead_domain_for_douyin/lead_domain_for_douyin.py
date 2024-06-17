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

def get_or_insert(doctype: str, orginal_search_kw: dict, new_doc_data: dict):
    doc = lead_tools.get_doc_or_none(doctype, orginal_search_kw)
    if not doc:
        doc = frappe.get_doc(new_doc_data.update({'doctype': doctype})).insert(ignore_permissions=True)
    return doc

def get_or_insert_clue_source(clue_source_id: str):
    doctype = 'Original Clue Sources'
    return get_or_insert(doctype, {'clue_source_id': clue_source_id}, {
        'clue_source_id': clue_source_id,
        'clue_source_name': '未录入的线索渠道'
    })


def get_or_insert_flow_type(flow_type_id: str):
    doctype = 'Original Flow Types'
    return get_or_insert(doctype, {'flow_type_id': flow_type_id}, {
        'flow_type_id': flow_type_id,
        'flow_type_name': '未录入的流量类型'
    })


def get_or_insert_clue_type(clue_type_id: str):
    doctype = 'Original Clue Types'
    return get_or_insert(doctype, {'clue_type_id': clue_type_id}, {
        'clue_type_id': clue_type_id,
        'clue_type_name': '未录入的线索类型'
    })

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
                }
            )
            clue_source_name = '线索来源未定义'
            if kwargs.get('clue_source'):
                clue_source = get_or_insert_clue_source(str(kwargs.get('clue_source')))
                clue_source_name = clue_source.name
                kwargs.update({'clue_source': clue_source.name})
            else:
                kwargs.pop('clue_source', None)
            
            if kwargs.get('flow_type'): 
                flow_type = get_or_insert_flow_type(str(kwargs.get('flow_type')))
                kwargs.update({'flow_type': flow_type.name})
            else:
                kwargs.pop('flow_type', None)
            
            if kwargs.get('clue_type'):
                clue_type = get_or_insert_clue_type(str(kwargs.get('clue_type')))
                kwargs.update({'clue_type': clue_type.name})
            else:
                kwargs.pop('clue_type', None)

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
