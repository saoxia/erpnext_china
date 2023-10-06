FROM digitwise/frappe
ENV WORK_DIR=/home/frappe/frappe-bench

COPY patches/workspace/buying/buying.json ${WORK_DIR}/apps/erpnext/erpnext/buying/workspace/buying/buying.json
COPY patches/workspace/crm/crm.json ${WORK_DIR}/apps/erpnext/erpnext/crm/workspace/crm/crm.json
COPY patches/workspace/manufacturing/manufacturing.json ${WORK_DIR}/apps/erpnext/erpnext/manufacturing/workspace/manufacturing/manufacturing.json
COPY patches/workspace/selling/selling.json ${WORK_DIR}/apps/erpnext/erpnext/selling/workspace/selling/selling.json
COPY patches/workspace/stock/stock.json ${WORK_DIR}/apps/erpnext/erpnext/stock/workspace/stock/stock.json

CMD ["/bin/bash"]