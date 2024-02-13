# Copyright (c) 2024, Digitwise Ltd. and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.modules.import_file import get_file_path, read_doc_from_file
import pandas as pd
import numpy as np
from frappe.permissions import get_roles,get_all_perms

class ButtonPermission(Document):
	pass

@frappe.whitelist()
def get_button_permission():
    # 获取当前用户的角色列表
    roles = get_roles(frappe.session.user)
    if 'System Manager' in roles:
        return {}
    else:
        # 获取角色对应的权限
        perms = []
        col_perms = ['parent','permlevel', 'read', 'write', 'create',
                    'select','delete','print','email','report','import','export','share','amend','cancel','submit']
        for line in frappe.get_all("Custom DocPerm", fields=col_perms, filters=[['role', 'in', roles]]):
            perms.append(list(line.values()))
            k = list(line.keys())
        roles_all_perms_df  = pd.DataFrame(perms,columns=k)
        _df = roles_all_perms_df.groupby(['parent','permlevel']).sum()
        _df = (_df > 0)*1
        _df.reset_index(inplace=True)
        _df['permlevel'] = _df.permlevel.astype(int)

        # 获取当前按钮所限制的权限
        cols = ['parent','label','group','doctype_name','level','read','write','create','select','delete_','print','email','report','import','export','share','amend','cancel','submit']
        button_permission_data = frappe.db.get_all('Button Permission Check Doctype',fields=cols)
        values = []
        for line in button_permission_data:
            values.append(list(line.values()))
        button_perms_df = pd.DataFrame(values,columns=cols)
        button_perms_df.rename(columns={'delete_':'delete'},inplace=True)
        button_perms_df['level'] = button_perms_df['level'].astype(int)
        
        # 判断是否有权限
        def check_perms(array):
            r = False
            has_perms = array[array==1].index.to_list()
            perms = _df[(_df['parent']==array['doctype_name'])&(_df['permlevel']==int(array['level']))]
            for idx,row in perms.iterrows():
                perms_ = row[row==1].index.to_list()
                if False not in np.isin(has_perms,perms_):
                    r = True
                
            if _(array['group']) == None:
                r2 = _(array['label']) + '__'
            else:
                r2 = _(array['label']) + '__' +_(array['group'])
            return r,r2
        button_perms_df[['has_perm','label_info']] = button_perms_df.apply(check_perms,axis=1,result_type='expand')
        # 筛选出没有权限lebels
        no_perms = button_perms_df[['parent','label_info']][~button_perms_df['has_perm']]
        def merge(idx):
            return idx.values.tolist()
        no_perms = no_perms.groupby(no_perms['parent']).agg(merge)
        return no_perms.to_dict(orient='index')
