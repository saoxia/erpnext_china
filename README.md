## ERPNext China Location（ERPNext中国本地化）
注意：由于一些单据实现方式原因，尽量全新安装测试。实现方式将在之后一段时间调整优化

### 功能介绍
#### 默认开启的功能：
1. 姓名录入修改为更适合中国人用的方式，员工增加身份证号、政治面貌等中国特有信息；
2. CRM、客户、线索表单增加微信、QQ字段为联系方式，创建联系人后会同步到联系人列表底层。同时隐藏google通讯等联系方式；
3. 区域列表自动添加完整的中国三级行政区划；
4. 第三方社交账号登录功能中添加使用企业微信登录的支持，[配置说明](.github/doc/企业微信登录配置说明.md)；
5. 对workspace中不支持zh.csv文件汉化的位置，如Your Shortcuts、Report&Master等进行汉化；人工翻译优化官方的机器翻译；


#### 版本兼容性
V15：已通过兼容测试</br>
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
