# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
import copy
import json
import traceback
from erpnext_china.utils.tools import get_doc_or_none
from frappe.exceptions import DoesNotExistError
from frappe.model.document import Document
import frappe

class LeadDomainforBaidu(Document):
	pass


@frappe.whitelist(allow_guest=True)
def lead_via_baidu(**kwargs):

    # 验证token
    if not verify_token(kwargs.get('token')):
        return 'The request from unknown sources!'

    original_clue_id = kwargs.get('clue_id')
    # 这里几乎不可能出现没有线索ID的情况
    if not original_clue_id:
        return 'Must have a clue id!'
    
    clue_id = str(original_clue_id)
    push_delay = kwargs.get('push_delay')
    try:
        record = get_doc_or_none('Original Leads', {'clue_id': clue_id})
        
        # 如果数据不存在则直接进行插入
        if not record:
            username = get_username_in_form_detail(kwargs, 'baidu')
            form_detail = kwargs.get('form_detail')
            if not isinstance(form_detail, str):
                form_detail = json.dumps(form_detail, ensure_ascii=False)
            kwargs.update(
                {   
                    'doctype': 'Original Leads', 
                    'source': 'Baidu',
                    'clue_id': clue_id,
                    'original_json_data': copy.deepcopy(kwargs),
                    'lead_name': username,
                    'form_detail': form_detail
                }
            )
            original_lead_doc = frappe.get_doc(kwargs).insert(ignore_permissions=True)
            flow_channel_name = get_or_insert_flow_channel_name(kwargs.get('flow_channel_name', '其它'), '百度')
            # 同时生成一条CRM数据
            crm_lead_doc = get_or_insert_crm_lead(
                username, 
                flow_channel_name, 
                kwargs.get('clue_phone_number'),
                kwargs.get('clue_phone_number'), 
                kwargs.get('wechat_account'),
                kwargs.get('area'), 
                kwargs.get('area_province'))
            
            # 添加crm 线索和原始线索之间的关系
            if crm_lead_doc:
                original_lead_doc.crm_lead = crm_lead_doc.name
                original_lead_doc.save()

        # 如果数据已经存在**并且**是通过延迟接口推送过来的则进行更新
        elif '延迟20分钟' in push_delay:
            
            update_delay_fields(record, kwargs)
            update_crm_lead_fields(record, kwargs)
        return 'success'
    except Exception as e:
        frappe.db.rollback()
        # 抛出异常，将异常扔给百度，让他重试
        raise e
    

def get_or_insert_flow_channel_name(flow_channel_name: str, prefix: str):
    # 首先判断是否已经有当前的流量渠道，没有则创建

    flow_channel_name = format_flow_channel_name(flow_channel_name, prefix)
    lead_source = get_doc_or_none('Lead Source', {
        'source_name': flow_channel_name
    })
    if not lead_source:
        lead_source_data = {
            'doctype': 'Lead Source',
            "source_name": flow_channel_name
        }
        lead_source = frappe.get_doc(lead_source_data).insert(ignore_permissions=True)
    return lead_source.name


def format_flow_channel_name(name: str, prefix: str):
    # 有这种情况：搜索推广   百度搜索推广
    # 字节-今日头条  其他渠道-手动导入
    if name.startswith(prefix):
        name = name.replace(prefix, '', 1)
    if name.startswith('-'):
        return prefix + name
    return '-'.join([prefix, name])


def update_delay_fields(record, kwargs):
    """
    更新原始线索
    """
    try:
        # 保存当前用户
        original_user = frappe.session.user
        # 切换到具有足够权限的用户
        frappe.set_user('Administrator')
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
        record.save()
        # 切换回原来的用户
        frappe.set_user(original_user)
    except:
        pass


def update_crm_lead_fields(record, kwargs):
    # 通过原始线索的crm_lead 字段找到crm线索
    crm_lead_name = record.crm_lead
    crm_lead = get_doc_or_none('Lead', {
        'name': crm_lead_name
    })
    # 更新字段
    if crm_lead:
        try:
            # 保存当前用户
            original_user = frappe.session.user
            # 切换到具有足够权限的用户
            frappe.set_user('Administrator')
            if kwargs.get('area'):
                crm_lead.city = kwargs.get('area')
            if kwargs.get('area_province'):
                crm_lead.state = kwargs.get('area_province')
            crm_lead.save()
            # 切换回原来的用户
            frappe.set_user(original_user)
        except: 
            pass


def verify_token(token: str):
    """
    验证token
    """
    return True


def save_parse_failed_data(doctype: str, clue_id: str, kwargs: dict, exception: str):
    """
    这里可以发送企业微信通知等
    """
    # data = {
    #     'doctype': doctype, 
    #     'clue_id': clue_id,
    #     'original_json_data': kwargs, 
    #     'exception_msg': exception,
    #     'parsed': 0,
    # }
    # try:
    #     doc = frappe.get_doc(data).insert(ignore_permissions=True)
    #     return doc
    # except:
    #     return None


def get_username_in_form_detail(kwargs: dict, source: str):
    """
    提取用户称呼，默认是线索的ID
    :param source: baidu | douyin
    """
    if source == 'baidu':
        form_detail = kwargs.get('form_detail')
        username = "匿名"
        # 目前只有solution_type_name是表单的来源才有称呼
        if '表单' in kwargs.get('solution_type_name', '') and form_detail:
            if isinstance(form_detail, str):
                form_detail = json.loads(form_detail)
            if isinstance(form_detail, list):
                for item in form_detail:
                    if item.get('type') == 'name' and item.get('value'):
                        username = item.get('value')
                        break
        return username

    return kwargs.get('name', '匿名') or "匿名"


def get_or_insert_crm_lead(lead_name, source, phone, mobile, wx, city, state, country='China'):
    """
    通过手机、电话、微信号查找线索是否已经存在
    """
    # 如果phone、mobile、wx都没有，则不需要创建CRM线索
    if not any([phone, mobile, wx]):
        return None

    or_filters = {}
    for field, value in [('phone', phone), ('mobile_no', mobile), ('custom_wechat', wx)]:
        if value:
            or_filters[field] = value
    
    # 检查是否存在匹配的记录
    records = frappe.get_list(
        "Lead",
        or_filters=or_filters,
        ignore_permissions=True
    )
    if len(records) > 0:
        record = records[0]
    else:
        # 构造新记录的数据
        crm_lead_data = {
            'doctype': 'Lead',
            'lead_name': lead_name,
            'source': source,
            'phone': phone or '',
            'mobile_no': mobile or '',
            'custom_wechat': wx or '',
            'city': city,
            'state': state,
            'country': country,
        }
        # 插入新记录
        record = frappe.get_doc(crm_lead_data).insert(ignore_permissions=True)
    return record


@frappe.whitelist(allow_guest=True)
def lead_via_douyin(**kwargs):

    original_id = kwargs.get('id')
    if not original_id:
        return

    clue_id = str(original_id)

    try:
        record = get_doc_or_none('Original Leads', {'clue_id': clue_id})
        # 如果数据不存在则直接进行插入
        if not record:
            username = get_username_in_form_detail(kwargs, 'douyin')
            gender = kwargs.get('gender', '未知')
            if gender == '男':
                gender = 'Male'
            elif gender == '女':
                gender = 'Female'
            kwargs.update(
                {
                    'doctype': 'Original Leads', 
                    'source': 'Douyin',
                    'original_json_data': copy.deepcopy(kwargs),
                    'clue_id': clue_id,
                    'lead_name': username,
                    'clue_phone_number': kwargs.get('telphone'),
                    'wechat_account': kwargs.get('weixin'),
                    'area': kwargs.get('city_name'),
                    'area_province': kwargs.get('province_name'),
                    'commit_time': kwargs.get('create_time'),
                    'site_url': kwargs.get('external_url'),
                    'gender': gender
                }
            )
            original_lead_doc = frappe.get_doc(kwargs).insert(ignore_permissions=True)
            clue_source = get_or_insert_flow_channel_name(kwargs.get('clue_source', '其它'))
            # 同时生成一条CRM数据
            crm_lead_doc = get_or_insert_crm_lead(
                username, 
                clue_source, 
                kwargs.get('telphone'),
                kwargs.get('telphone'), 
                kwargs.get('weixin'), 
                kwargs.get('city_name'), 
                kwargs.get('province_name'))
            
            # 添加crm 线索和原始线索之间的关系
            if crm_lead_doc:
                original_lead_doc.crm_lead = crm_lead_doc.name
                original_lead_doc.save()
        
        return  {'code': 0,'message': 'success'}
    except Exception as e:
        # 如果出现异常，回滚之前的操作
        frappe.db.rollback()
        raise e

