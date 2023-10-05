#飞鱼商机导入

import pandas as pd
df_ = pd.DataFrame()
df = pd.read_excel(r'C:\Users\lly\Downloads\飞鱼CRM销售线索数据 (4).xlsx')

df['自动定位城市'] = df['自动定位城市'].fillna(value=df['手机号归属地'])
df = df[['姓名','电话','线索ID','通话状态','所属人','自动定位城市']]

df_['ID'] = df['线索ID'].map(lambda x : "CRM-LEAD-2023-"+str(x))
df_['系列'] = 'CRM-LEAD-.YYYY.-'
df_['姓名'] = df['姓名']
df_['lead_name'] = df['姓名']
df_['线索负责人'] = 'Administrator'  #这里要修改df['所属人']
df_['手机号码'] = df['电话']
df_['省'] = df['自动定位城市'].map(lambda x : x.split('-')[0])
df_['城市'] = df['自动定位城市'].map(lambda x : x.split('-')[1])

df_.to_excel('lead.xlsx',index=False)