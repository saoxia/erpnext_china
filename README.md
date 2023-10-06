## ERPNext China Location（ERPNext中国本地化）

### 功能介绍
#### 默认开启的功能：
1. 姓名录入修改为更适合中国人用的方式，员工增加身份证号、政治面貌等中国特有信息；
2. CRM、客户、线索表单增加微信、QQ字段为联系方式，创建联系人后会同步到联系人列表底层。同时去除google通讯等联系方式；
3. 区域列表自动添加完整的中国三级行政区划；
4. 第三方社交账号登录功能中添加使用企业微信登录的支持；
5. 对workspace中不支持zh.csv文件汉化的位置，如Your Shortcuts、Report&Master等进行汉化；

#### 默认关闭的功能：
1. 飞鱼crm的销售线索自动更新到ERPNext的crm线索板块

#### 版本兼容性
V15：已通过兼容测试
V14：理论兼容，未测试


### 安装步骤

首先，获取app
```sh
$ bench get-app https://github.com/digitwise/erpnext_china.git
```

然后，安装erpnext和erpnext_china
```sh
$ bench --site demo.com install-app erpnext erpnext_china
```