# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
import copy
import json
import traceback
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
    
    # bd- 防止与抖音的线索ID撞车
    clue_id = 'bd-' + str(original_clue_id)
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
            # 同时生成一条CRM数据
            crm_lead_doc = insert_or_get_crm_lead(
                username, 
                '百度营销', 
                kwargs.get('clue_phone_number'),
                kwargs.get('clue_phone_number'), 
                kwargs.get('wechat_account'),
                kwargs.get('area'), 
                kwargs.get('area_province'))
            
            # 添加crm 线索和原始线索之间的关系
            original_lead_doc.crm_lead = crm_lead_doc.name
            original_lead_doc.save()

        # 如果数据已经存在**并且**是通过延迟接口推送过来的则进行更新
        elif '延迟20分钟' in push_delay:
            
            update_delay_fields(record, kwargs)
            update_crm_lead_fields(record, kwargs)

    except Exception as e:
        frappe.db.rollback()
        # 这里可以在企业微信里进行通知
        # save_parse_failed_data('Original Leads', clue_id, kwargs, traceback.format_exc())
        # 抛出异常，将异常扔给百度，让他重试
        raise e
    return 'success'


def update_delay_fields(record, kwargs):
    """
    更新原始线索
    """
    try:
        # 保存当前用户
        original_user = frappe.session.user
        # 切换到具有足够权限的用户
        frappe.set_user('Administrator')
        record.ad_uc_name = kwargs.get('ad_uc_name')
        record.area_province = kwargs.get('area_province')
        record.area = kwargs.get('area')
        record.plan_id = kwargs.get('plan_id')
        record.plan_name = kwargs.get('plan_name')
        record.unit_id = kwargs.get('unit_id')
        record.unit_name = kwargs.get('unit_name')
        record.creative_id = kwargs.get('creative_id')
        record.creative_name = kwargs.get('creative_name')
        record.keyword_id = kwargs.get('keyword_id')
        record.keyword = kwargs.get('keyword')
        record.search_word = kwargs.get('search_word')
        record.refund_supportive = kwargs.get('refund_supportive')
        
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
            crm_lead.city = kwargs.get('area')
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


def get_doc_or_none(doc: str, kw: dict):
    """如果没有通过kw查询到doc，将DoesNotExistError错误处理返回None"""
    try:
        doc = frappe.get_last_doc(doc, filters=kw)
        return doc
    except DoesNotExistError as e:
        return None


def get_username_in_form_detail(kwargs: dict, source: str):
    """
    提取用户称呼，默认是线索的ID
    :param source: baidu | douyin
    """
    if source == 'baidu':
        form_detail = kwargs.get('form_detail')
        username = kwargs.get('clue_id')
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

    return kwargs.get('name') or kwargs.get('id')


def insert_or_get_crm_lead(lead_name, source, phone, mobile, wx, city, state, country='China'):
    """
    通过手机号查找联系人是否已经存在
    """
    record = get_doc_or_none('Lead', {
        'phone': phone
    })
    if not record:
        crm_lead_data = {
            'doctype': 'Lead',
            'lead_name': lead_name,
            'source': source,
            'phone': phone,
            'mobile_no': mobile,
            'whatsapp_no': wx,
            'city': city,
            'state': state,
            'country': country,
        }
        record = frappe.get_doc(crm_lead_data).insert(ignore_permissions=True)
    return record


@frappe.whitelist(allow_guest=True)
def lead_via_douyin(**kwargs):

    original_id = kwargs.get('id')
    if not original_id:
        return

    clue_id = 'dy-' + str(original_id)

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
            
            # 同时生成一条CRM数据
            crm_lead_doc = insert_or_get_crm_lead(
                username, 
                '抖音广告', 
                kwargs.get('telphone'),
                kwargs.get('telphone'), 
                kwargs.get('weixin'), 
                kwargs.get('city_name'), 
                kwargs.get('province_name'))
            
            # 添加crm 线索和原始线索之间的关系
            original_lead_doc.crm_lead = crm_lead_doc.name
            original_lead_doc.save()
    except Exception as e:
        # 如果出现异常，回滚之前的操作
        frappe.db.rollback()
        raise e
        # save_parse_failed_data('Original Leads', clue_id, kwargs, traceback.format_exc())
    return  {'code': 0,'message': 'success'}
