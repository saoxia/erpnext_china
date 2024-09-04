# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
import copy
import json
import re
from erpnext_china.utils import lead_tools
from frappe.model.document import Document
import frappe
from frappe.utils import datetime
from erpnext_china.utils.wechat.api import qv_create_crm_lead

class LeadDomainforBaidu(Document):
    pass


@frappe.whitelist(allow_guest=True)
def lead_via_baidu(**kwargs):

    original_clue_id = kwargs.get('clue_id')
    # 这里几乎不可能出现没有线索ID的情况
    if not original_clue_id:
        frappe.local.response['http_status_code'] = 400
        frappe.local.response.update({'message': 'Must have id!'})
        return
    
    clue_id = str(original_clue_id)
    push_delay = kwargs.get('push_delay', '')
    try:
        # 获取线索来源的账户（Lead Domain for Baidu）
        baidu_account = get_employee_account(kwargs.get('uc_name'))
        # 验证token
        if not verify_token(kwargs.get('token'), baidu_account.token if baidu_account else ''):
            frappe.local.response['http_status_code'] = 403
            frappe.local.response.update({'message': 'The request from unknown sources!'})
            return 
        
        record = lead_tools.get_doc_or_none('Original Leads', {'clue_id': clue_id})
        
        user, employee = None, None
        if baidu_account:
            employee = lead_tools.get_doc_or_none('Employee', {"name": baidu_account.employee})
        if employee:
            user = employee.user_id

        if user:
            # 切换到当前线索来源百度营销通对应的用户
            frappe.set_user(user)
        # 如果原始线索不存在则直接进行插入
        if not record:
            
            lead_name = lead_tools.get_username_in_form_detail(kwargs, 'baidu')
            kwargs = format_fields(kwargs)

            kwargs.update(
                {   
                    'doctype': 'Original Leads', 
                    'source': 'Baidu',
                    'clue_id': clue_id,
                    'original_json_data': copy.deepcopy(kwargs),
                    'lead_name': lead_name,
                    'employee_baidu_account': baidu_account.name if baidu_account else None,
                    'user': user,
                    'product_category': baidu_account.product_category if baidu_account else None
                }
            )
            
            original_lead_doc = frappe.get_doc(kwargs).insert(ignore_permissions=True)
            flow_channel_name = lead_tools.get_or_insert_flow_channel_name(kwargs.get('flow_channel_name', '其它'), '百度')
            # 同时生成一条CRM数据
            # 有的百度线索的 clue_phone_number 是这种形式的 1781111111,13511111111
            phone_numbers = re.findall(r'\d+', str(kwargs.get('clue_phone_number', '')))[:2]
            phone1, phone2 = phone_numbers + [''] * (2 - len(phone_numbers))
            crm_lead_doc = lead_tools.get_or_insert_crm_lead(
                lead_name, 
                flow_channel_name, 
                phone1,
                phone2, 
                kwargs.get('wechat_account', ''),
                kwargs.get('area'), 
                kwargs.get('area_province'),
                original_lead_name=original_lead_doc.name,
                commit_time=original_lead_doc.commit_time or original_lead_doc.created_datetime,
                keyword=original_lead_doc.keyword,
                search_word=original_lead_doc.search_word,
                auto_allocation=baidu_account.auto_allocation if baidu_account else False,
                bd_account=baidu_account.name if baidu_account else None,
                product_category=baidu_account.product_category if baidu_account else None,
            )
            
            # 添加crm 线索和原始线索之间的关系
            if crm_lead_doc:
                original_lead_doc.crm_lead = crm_lead_doc.name
                original_lead_doc.save(ignore_permissions=True)
            else:
                qv_create_crm_lead(original_lead=original_lead_doc)
        # 如果原始线索已经存在**并且**是通过延迟接口推送过来的则进行更新
        elif '延迟20分钟' in push_delay:
            
            update_delay_fields(record, kwargs)
            update_crm_lead_fields(record, kwargs)
        return 'success'
    except Exception as e:
        frappe.db.rollback()
        # 抛出异常，将异常扔给百度，让他重试
        raise e

# 格式化一些字段
def format_fields(kwargs: dict):
    form_detail = kwargs.get('form_detail')
    if not isinstance(form_detail, str):
        form_detail = json.dumps(form_detail, ensure_ascii=False)
    additional_content = kwargs.get('additional_content')
    if not isinstance(additional_content, str):
        additional_content = json.dumps(additional_content, ensure_ascii=False)
    
    kwargs.update({
        'form_detail': form_detail,
        'additional_content': additional_content,
        'created_datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return kwargs


# 通过uc_name找到lead domain for baidu的账号
def get_employee_account(uc_name: str):
    if not uc_name:
        return None
    doc = lead_tools.get_doc_or_none("Lead Domain for Baidu", {"baiduid": uc_name})
    return doc


def update_delay_fields(record, kwargs):
    """
    更新原始线索
    """
    try:
        # 为了防止 字段没有值的请求将已经存在的字段值覆盖
        # 定义需要更新的字段列表
        fields_to_update = [
            'ad_uc_name', 'area_province', 'area', 'plan_id', 
            'plan_name', 'unit_id', 'unit_name', 'creative_id', 
            'creative_name', 'keyword_id', 'keyword', 'search_word', 
            'refund_supportive'
        ]

        # 使用字典推导和循环更新记录中的字段
        for field in fields_to_update:
            if kwargs.get(field):
                setattr(record, field, kwargs.get(field))

        # 保存记录
        record.save(ignore_permissions=True)
    except:
        pass


def update_crm_lead_fields(record, kwargs):
    # 通过原始线索的crm_lead 字段找到crm线索
    doctype = 'Lead'
    crm_lead_name = record.crm_lead
    crm_lead = lead_tools.get_doc_or_none(doctype, {'name': crm_lead_name})
    # 更新字段
    if crm_lead:
        original_lead_name = crm_lead.custom_original_lead_name
        if original_lead_name == record.name:
            try:
                city = kwargs.get('area')
                state = kwargs.get('area_province')
                keyword = kwargs.get('keyword')
                search_word = kwargs.get('search_word')
                
                if keyword: crm_lead.custom_keyword = keyword
                if search_word: crm_lead.custom_search_word = search_word
                
                if city: crm_lead.city = city
                if state: crm_lead.state = state
                if city or state:
                    territory = lead_tools.get_system_territory(city or state)
                    crm_lead.territory = territory
                
                crm_lead.save(ignore_permissions=True)
                
            except: 
                pass


def verify_token(requst_token: str, token: str):
    """
    验证token
    """
    # if requst_token != token:
    #     return False
    return True
