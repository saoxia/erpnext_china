ARG PYTHON_VERSION=3.11.5
ARG DEBIAN_BASE=bookworm
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

ARG WKHTMLTOPDF_VERSION=0.12.6.1-3
ARG WKHTMLTOPDF_DISTRO=bookworm
ARG NODE_VERSION=18.17.1
ENV NVM_DIR=/home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

RUN useradd -ms /bin/bash frappe \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    openssh-server \
    curl \
    git \
    vim \
    sudo \
    gettext-base \
    # weasyprint dependencies
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    # For backups
    restic \
    # MariaDB
    mariadb-client \
    # Postgres
    libpq-dev \
    postgresql-client \
    # For healthcheck
    wait-for-it \
    jq \
    # NodeJS
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.2/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && echo 'export NVM_DIR="/home/frappe/.nvm"' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion' >>/home/frappe/.bashrc \
    # Install wkhtmltopdf with patched qt
    && if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_${WKHTMLTOPDF_VERSION}.${WKHTMLTOPDF_DISTRO}_${ARCH}.deb \
    && curl -sLO https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && apt-get install -y ./$downloaded_file \
    && rm $downloaded_file \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && rm -fr /etc/nginx/sites-enabled/default \
    && pip3 install frappe-bench ansible 

FROM base AS builder

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    # For frappe framework
    wget \
    # For psycopg2
    libpq-dev \
    # Other
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    redis-tools \
    rlwrap \
    tk8.6-dev \
    cron \
    # For pandas
    gcc \
    build-essential \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

USER frappe

ARG FRAPPE_BRANCH=version-15-beta
ARG FRAPPE_PATH=https://github.com/frappe/frappe
ARG ERPNEXT_REPO=https://github.com/saoxia/erpnext-chinese
ARG ERPNEXT_BRANCH=version-15-chinese
RUN bench init \
  --frappe-branch=${FRAPPE_BRANCH} \
  --frappe-path=${FRAPPE_PATH} \
  --skip-redis-config-generation \
  /home/frappe/frappe-bench && \
  cd /home/frappe/frappe-bench && \
  bench get-app --branch=${ERPNEXT_BRANCH} ${ERPNEXT_REPO} && \
  bench get-app --branch develop https://github.com/saoxia/erpnext_china && \
  bench get-app --branch version-15-beta https://github.com/frappe/hrms && \
  find apps -mindepth 1 -path "*/.git" | xargs rm -fr

COPY patch/frappe/login.html /home/frappe/frappe-bench/apps/frappe/frappe/www/login.html
COPY patch/frappe/user.json /home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/user/user.json
COPY patch/frappe/users.json /home/frappe/frappe-bench/apps/frappe/frappe/core/workspace/users/users.json
COPY patch/frappe/system_settings.json /home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/system_settings/system_settings.json
COPY patch/frappe/install_fixtures.py /home/frappe/frappe-bench/apps/frappe/frappe/desk/page/setup_wizard/install_fixtures.py
COPY patch/frappe/setup_wizard.js /home/frappe/frappe-bench/apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.js
COPY patch/frappe/setup_wizard.py /home/frappe/frappe-bench/apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.py
COPY patch/frappe/contact.json /home/frappe/frappe-bench/apps/frappe/frappe/contacts/doctype/contact/contact.json
COPY patch/frappe/install.py /home/frappe/frappe-bench/apps/frappe/frappe/utils/install.py
COPY patch/frappe/about.js /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/toolbar/about.js

COPY common_site_config.json /home/frappe/frappe-bench/sites/common_site_config.json

FROM base as erpnext
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN sed 's/#Port 22/Port 22222/' /etc/ssh/sshd_config > /etc/ssh/sshd_config_temp && mv /etc/ssh/sshd_config_temp /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && ssh-keygen -A
RUN echo 'root:bi123456' | chpasswd 
RUN echo 'frappe:bi123456' | chpasswd 
RUN  service ssh restart 

USER frappe

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

CMD ["/bin/bash"]