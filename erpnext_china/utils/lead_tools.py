
import datetime
import json
import frappe
from frappe.model.document import Document


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

###### 未完成，需要调整 ######
def crm_lead_linked_customer(crm_lead):
    """通过联系方式找到客户
    """

    # 通过线索创建的联系人在dynamic link中表现为 link_doctype=Lead parent=称呼
    # 手动创建的联系人不会有dynamic link的记录
    # 1.在线索中创建客户，则会在dynamic link 中创建一条 link_doctype=Customer parent=称呼的记录
    # 同时，客户关联上了线索 lead_name=Lead.name
    # 2.手动在客户中创建客户，并关联线索同1.类似
    or_filters = {}
    for field, value in [
        ('phone', crm_lead.phone), 
        ('mobile_no', crm_lead.mobile), 
        ('custom_wechat', crm_lead.custom_wechat)
    ]:
        if value:
            or_filters[field] = value
    
    # 检查是否存在匹配的记录
    # 联系人的联系方式可以重复
    contacts = frappe.get_all(
        "Contact",
        or_filters=or_filters
    )
    if len(contacts) > 0:
        for contact in contacts:
            # 找到这个联系人是否已经和客户关联了
            dynamic_links = frappe.get_all('Dynamic Link',
                filters=[
                    ["link_doctype", "=", "Customer"],
                    ["parent", "=", contact.name],
                ],
                fields=['link_name'],
            )
            # 找到联系人已经关联的客户
            customers = frappe.get_all('Customer', filtres=['name', 'in', [dl.link_name for dl in dynamic_links]])
            # 客户关联线索
            # 如果已经关联过线索，则修改为关联现在的新线索
            # 如果是没有关联过线索，则关联线索
            for customer in customers:
                customer.lead_name = crm_lead.name
                customer.save()



def get_or_insert_crm_lead(
        lead_name, source, phone:str, mobile:str, wx:str, 
        city, state, original_lead_name, commit_time, product_category='',
        auto_allocation=False, bd_account=None, dy_account=None, country='China'):
    """
    如果存在返回doc，并添加评论有新的原始线索关联过来了，不存在则创建

    :param lead_name: 线索客户称呼
    :param source: 线索来源
    :param phone: 电话
    :param mobile: 手机号
    :param wx: 微信号
    :param city: 市
    :param state: 省
    :param country: 国家
    :param original_lead_name: 创建当前线索的原始线索name
    :param bd_account: 百度平台账户
    :param dy_account: 飞鱼平台账户
    :param auto_allocation: 是否自动分配
    """
    phone = str(phone).replace(' ', '')
    mobile = str(mobile).replace(' ', '')
    wx = str(wx).replace(' ', '')
    # 如果phone、mobile、wx都没有，则不需要创建CRM线索
    if not any([phone, mobile, wx]):
        return None

    # or_filters = {}
    # for field, value in [('phone', phone), ('mobile_no', mobile), ('custom_wechat', wx)]:
    #     if value:
    #         or_filters[field] = value
    links = list(set([i for i in [phone, mobile, wx] if i]))
    or_filters = [
        {'phone': ['in', links]},
        {'mobile_no': ['in', links]},
        {'custom_wechat': ['in', links]}
    ]
    # 检查是否存在匹配的线索
    records = frappe.get_all(
        "Lead",
        or_filters=or_filters
    )
    if len(records) > 0:
        record = records[0]
        # 已经存在相同联系方式的线索，给个评论提示一下
        insert_crm_note(f"有新的原始线索:【{original_lead_name}】关联到当前线索", record.name)
    else:
        territory = get_system_territory(city or state or country)
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
            'territory': territory,
            'custom_employee_baidu_account': bd_account,
            'custom_employee_douyin_account': dy_account,
            'lead_owner': '', # 这个给个默认线索负责人为空
            'custom_auto_allocation': auto_allocation,
            'custom_product_category': product_category,
            'custom_last_lead_owner': '',
            'custom_commit_time': commit_time,  # 线索提交到平台的时间
        }
        # 插入新记录
        record = frappe.get_doc(crm_lead_data).insert(ignore_permissions=True)
    return record


def get_system_territory(territory: str):
    if territory == 'China':
        return '中国'
    if territory:
        like_pattern = f"%{territory}%"
        territories = frappe.get_all(
            'Territory',
            filters=[
                ['territory_name', 'like', like_pattern]
            ]
        )
        if len(territories) > 0:
            territory = territories[0].name
            return territory
    return None

def insert_crm_note(note: str, parent: str):
    try:
        note_data = {
            'doctype': 'CRM Note',
            'note': note,
            'added_by': frappe.session.user,
            'added_on': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'parent': parent,
            'parentfield': 'notes',
            'parenttype': 'Lead'
        }
        frappe.get_doc(note_data).insert(ignore_permissions=True)
    except:
        pass

def verify_has_permission(doctype: str, ptype: str, doc: Document, user=None) -> bool:
    """验证user对指定doctype的doc是否有ptype的权限
    
    :param user: 默认是当前用户
    """
    try:
        return frappe.has_permission(doctype=doctype, ptype=ptype, doc=doc, user=user)
    except:
        return False