运行frappe
docker run -it --name frappe \
    -v/root/frappe/common_site_config.json:/home/frappe/frappe-bench/sites/common_site_config.json \
    --network=host \
    registry.cn-hangzhou.aliyuncs.com/saoxia/lly:frappe

运行db
docker run -d --name db \
    -p3308:3306  \
    --env MARIADB_ROOT_PASSWORD=bi123456  \
    -v/root/frappe/db/mysql:/var/lib/mysql \
    mariadb:10.6
备注：修改/etc/mysql/my.cnf文件
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4



运行redis
docker run --name redis -d --network=host redis

安装app
bench new-app digitwise
安装site
bench new-site --db-port=3308 --db-name=mis mysite.local
site添加到hosts
127.0.0.1 mysite.local
app添加到site
bench --site mysite.local install-app digitwise  erpnext hrms 
安装erpnext
bench get-app --branch version-15-beta https://github.com/saoxia/erpnext

git
查看修改
git status
设置git
git remote add origin https://github.com/saoxia/erpnext.git
git remote set-url origin https://github.com/saoxia/erpnext.git

git config --global user.email "407469895@qq.com"
git config --global user.name "saoxia"
说明
git commit -a -m "employee add lable of idcard."
提交
git push origin version-15-beta
git撤销提交
git revert 哈希值

token
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

配置nginx
docker run -d --name nginx -p19200:80  -v/root/frappe/nginx.conf:/etc/nginx/nginx.conf  nginx