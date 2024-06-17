
import json
import frappe


def get_doc_or_none(doctype: str, kw: dict):
    """根据kw查找doctype中是否存在记录，如果存在则返回document对象，否则返回None"""
    doc_name = frappe.db.exists(doctype, kw)
    if doc_name:
        doc = frappe.get_doc(doctype, doc_name)
        return doc
    else:
        return None


def get_or_insert_flow_channel_name(flow_channel_name: str, prefix: str):
    """判断是否已经有当前的流量渠道，没有则格式化后创建"""

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
    """格式化流量渠道名称 
    
        有这种情况：搜索推广 百度搜索推广 字节-今日头条  其他渠道-手动导入

        统一为 百度-搜索推广，字节-今日头条
    """
    if name.startswith(prefix):
        name = name.replace(prefix, '', 1)
    if name.startswith('-'):
        return prefix + name
    return '-'.join([prefix, name])


def get_username_in_form_detail(kwargs: dict, source: str):
    """
    提取用户称呼，默认是线索的ID
    :param source: baidu | douyin
    """
    if source not in ['baidu', 'douyin']:
        return "未知"
    
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
    通过手机、电话、微信号查找线索是否已经存在，如果存在返回doc，不存在则创建
    """
    # 如果phone、mobile、wx都没有，则不需要创建CRM线索
    if not any([phone, mobile, wx]):
        return None

    or_filters = {}
    for field, value in [('phone', phone), ('mobile_no', mobile), ('custom_wechat', wx)]:
        if value:
            or_filters[field] = value
    
    # 检查是否存在匹配的记录
    records = frappe.get_all(
        "Lead",
        or_filters=or_filters
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