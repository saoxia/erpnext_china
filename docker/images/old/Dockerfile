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
RUN bench init --frappe-branch version-15 frappe-bench --frappe-path=https://github.com/frappe/frappe

WORKDIR /home/frappe/frappe-bench

RUN bench get-app --branch develop https://github.com/frappe/erpnext
RUN bench get-app --branch develop https://github.com/saoxia/erpnext_china


#CMD ["bench", "start"]
