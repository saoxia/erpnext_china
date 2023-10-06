FROM ubuntu:22.04

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 安装ssh，
#    && mkdir /run/sshd \
#    && apt-get install -y openssh-server \
#    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
#   && ssh-keygen -A
RUN apt-get update \
    && echo 'root:bi123456' | chpasswd \


RUN apt update
RUN apt-get install sudo curl -y


RUN curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
RUN apt-get install -y nodejs
# 安装yarn
RUN npm install -g yarn

# 安装wkhtmltopdf
RUN apt-get install -y xvfb libfontconfig wkhtmltopdf
RUN apt install -y python3.10-dev python3-setuptools python3-pip python3-distutils python3.10-venv software-properties-common mariadb-server mariadb-client redis-server nodejs xvfb libfontconfig wkhtmltopdf libmysqlclient-dev cron vim git ttf-wqy-zenhei ttf-wqy-microhei
RUN pip3 install frappe-bench

RUN groupadd -r -g 1000 frappe && useradd -r -u 1000 -g frappe frappe
RUN echo 'frappe:666666' | chpasswd
WORKDIR /home/frappe
RUN chmod -R 777 .
USER frappe
RUN bench init --frappe-branch version-15-beta frappe-bench --frappe-path=https://github.com/frappe/frappe

WORKDIR /home/frappe/frappe-bench

#RUN bench get-app --branch develop https://github.com/frappe/hrms
#RUN bench get-app --branch develop https://github.com/frappe/erpnext
RUN bench get-app --branch main https://github.com/saoxia/digitwise
RUN bench get-app --branch version-15-beta https://github.com/saoxia/hrms
RUN bench get-app --branch 15 https://github.com/saoxia/erpnext
RUN bench get-app insights

COPY patch/user.json ./apps/frappe/frappe/core/doctype/user/user.json
COPY patch/install_fixtures.py ./apps/frappe/frappe/desk/page/setup_wizard/install_fixtures.py
COPY patch/contact.json ./apps/frappe/frappe/contacts/doctype/contact/contact.json
COPY common_site_config.json ./sites/common_site_config.json
COPY Procfile ./Procfile
#CMD ["bench", "start"]
