# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import frappe
import os
import json
from frappe import _, has_permission,get_doc
from frappe.desk import query_report
from frappe.query_builder.functions import Count
from pypika.terms import Bracket
from frappe.desk.query_report import add_total_row


original_run = query_report.run
@frappe.whitelist()
@frappe.read_only()
def custom_run(report_name, filters=None, user=None, ignore_prepared_report=False, custom_columns=None):
    if not user:
        user = frappe.session.user
    result = original_run(report_name, filters=filters, user=user, 
                ignore_prepared_report=ignore_prepared_report, custom_columns=custom_columns)
    columns, data, is_add_total_row = result.get('columns'), result.get('result'),result.get('add_total_row')
    if columns and  data:
        if is_add_total_row: data = data[:-1]
        columns, data = remove_unauthorized_fields(report_name, user, columns, data)
        columns, data = remove_unauthorized_rows(report_name, user, columns, data)
        if is_add_total_row:
            data = add_total_row(data, columns)
        result['columns'] = columns
        result['result'] = data
        #全部图表，及表格字段标签统一调用翻译函数，有点性能损失，但不用修改官方源码
        for column in columns:
            if column.get('label'): column['label'] = _(column['label'])
        if result.get('chart') and result.get('chart',{}).get('data'):
            data = result['chart']['data']
            if data.get('labels'):
                data['labels'] = [_(label) for label in data['labels']]
            if data.get('datasets'):
                for dataset in data['datasets'] or []:
                    if dataset.get('name'): dataset['name'] = _(dataset.get('name'))        
    return result

query_report.run = custom_run

def get_unauthorized_fields(report_name, user):         
    #qb does not support where a=xx and  (b is null or b=xx), only a =xx and b is null or b=xx , use Bracket 
    restrict_field = frappe.qb.DocType('Restrict Field')
    restrict_field_set = frappe.qb.DocType('Restrict Field Set')
    restrict_field_report = frappe.qb.DocType('Restrict Field Report')
    restrict_fields = frappe.qb.from_(
            restrict_field_set
        ).join(
            restrict_field
        ).on(
            restrict_field.parent == restrict_field_set.name
        ).left_join(
            restrict_field_report
        ).on(
            restrict_field_report.parent == restrict_field_set.name
        ).distinct().select(
            restrict_field.fieldname
        ).where(
            (restrict_field_set.active == 1) & 
            Bracket(restrict_field_report.name.isnull() | restrict_field_report.report == report_name)
        ).run()        
    if restrict_fields:
        restrict_field_assign = frappe.qb.DocType('Restrict Field Assign')
        restrict_field_assign_report = frappe.qb.DocType('Restrict Field Assign Report')
        restrict_field_assign_role = frappe.qb.DocType('Restrict Field Assign Role')
        #restrict_field_assign_user = frappe.qb.DocType('Restrict Field Assign User')
        has_role = frappe.qb.DocType('Has Role')
        assign_fields = frappe.qb.from_(
                restrict_field_assign
            ).join(
                restrict_field_set
            ).on(
                restrict_field_assign.restrict_field_set == restrict_field_set.name
            ).join(
                restrict_field
            ).on(
                restrict_field.parent == restrict_field_assign.restrict_field_set
            ).join(
                restrict_field_assign_role
            ).on(
                restrict_field_assign_role.parent == restrict_field_assign.name
            ).join(
                has_role
            ).on(
                has_role.role == restrict_field_assign_role.role
            ).left_join(
                restrict_field_assign_report
            ).on(
                restrict_field_assign_report.parent == restrict_field_assign.name        
            ).distinct().select(
                restrict_field.fieldname
            ).where(
                (restrict_field_set.active == 1) & (has_role.parent == user) & 
                    Bracket(restrict_field_assign_report.name.isnull() | restrict_field_assign_report.report == report_name)
            ).run()        
        restrict_fields = {f[0] for f in restrict_fields}
        assign_fields = {f[0] for f in assign_fields}
        remove_fields = restrict_fields - assign_fields
    else:
        remove_fields = set()

    return remove_fields

def get_lang():
    """get lang for column label"""
    lang = 'zh'
    user_lang = frappe.translate.get_user_lang()
    if user_lang and user_lang != 'en':
        lang = user_lang
    else:
        default_lang =  frappe.db.get_default("lang") 
        if default_lang and default_lang != 'en':
            lang = default_lang
     
    return lang

def remove_unauthorized_fields(report_name, user, columns, data):
    """
        1. restrict fields of current report and all reports(empty report field)
        2. assign fields of current user role 
        3. unauthorized fields = restrict fields - assign fields
        4. remove field from columns and data( both dict and list type) 
    """
    def to_remove(column):
        """check fieldname against fieldname, label and translated label"""
        for f in remove_fields:
            if f in column.get('fieldname') or f in column.get('label') or f in _(column.get('label'), get_lang()):
                return True
        return False
     
    remove_fields = get_unauthorized_fields(report_name, user)
    if remove_fields:
        remove_fields = {c.get('fieldname') for c in columns if to_remove(c)}
        if remove_fields:
            if isinstance(data[0], list):      
                col_idx = [i for i, c in enumerate(columns) if not c.get('fieldname') not in remove_fields]
            columns = [c for c in columns if c.get('fieldname') not in remove_fields]
            if isinstance(data[0], dict):
                data = [{fieldname:fieldvalue for fieldname, fieldvalue in d.items() if fieldname not in remove_fields} for d in data]
            elif isinstance(data[0], list):
                data = [{value for i, value in enumerate(d) if i in col_idx} for d in data]
    return columns, data

def remove_unauthorized_rows(report_name, user, columns, data):
    """
        remove unauthorized rows if has_permission(doc) return False
        has_permission applies user permission and also calls hooked custom has_permission() 
        which in turn applies custom list query conditions 
    """        
    check_field = frappe.db.get_value('Report Apply User Permission', report_name, ['check_field']) or None
    docname_field, doctype, doctype_field = (None,None,None)
    if check_field:
        f = check_field
        for column in columns:
            if f in column.get('fieldname') or f in column.get('label') or f in _(column.get('label'), get_lang()):
                docname_field = column.get('fieldname')
                fieldtype = column.get('fieldtype')
                if fieldtype == 'Link':
                    doctype = column.get('options')
                elif fieldtype == 'Dynamic Link':
                    options = column.get('options')
                    for c in columns:
                        if c.get('fieldname') == options:
                            doctype_field = c.get('fieldname')
                            break
                break
        if docname_field and (doctype or doctype_field):    
            try:
                if isinstance(data[0], dict):
                    data = [d for d in data 
                        if has_permission(doc = get_doc( doctype or d.get(doctype_field), d.get(docname_field) ) )]
                elif isinstance(data[0], list):
                    doctype_idx, docname_idx = (None, None)
                    for (idx, column) in enumerate(columns):
                        if column.fieldname == doctype_field:
                            doctype_idx = idx
                        elif column.fieldname == docname_field:
                            docname_idx = idx
                        elif doctype_idx and docname_idx:
                            break
                    if docname_idx:
                        data = [d for d in data if has_permission(doc = get_doc(doctype or d[doctype_idx], d[docname_idx]))]
            except Exception as e:
                frappe.msgprint(f"{report_name} apply user permission program error {str(e)}")
    return columns, data

@frappe.whitelist()
def get_data_for_custom_field_wrapper(doctype, fieldname, field=None):
    from frappe.desk.query_report import get_data_for_custom_field

    dummy_doc = frappe.get_doc({'doctype': doctype})
    try:
        if dummy_doc.has_permlevel_access_to(field or fieldname):
            return get_data_for_custom_field(doctype = doctype, fieldname=fieldname, field=field)
        else:
            frappe.msgprint(_('No field permission'))
    except Exception as e:
        frappe.msgprint(f"Add Column for {doctype} {fieldname} with error {str(e)}")        

"""
frappe.set_user('test@163.com')
from frappe.desk.query_report import run
from zelin_permission.override import *
report_name='Stock Balance'
user='test@163.com'
filters={"company":"frappedemo","from_date":"2021-12-10","to_date":"2022-01-10"}
result = run(report_name, filters=filters, user=user, ignore_prepared_report=True)
columns, data, is_add_total_row = result.get('columns'), result.get('result'),result.get('add_total_row')
data = data[:-1]
columns1, data1 = remove_unauthorized_restrict_fields(report_name, user, columns, data)
report_name='Sales Analytics'
filters={"tree_type":"Customer","doc_type":"Sales Invoice","value_quantity":"Value","from_date":"2021-01-01","to_date":"2021-12-31","company":"frappedemo","range":"Monthly"}
"""