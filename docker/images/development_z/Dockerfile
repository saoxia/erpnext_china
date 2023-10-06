FROM digitwise/frappe
ENV WORK_DIR=/home/frappe/frappe-bench

COPY patches/workspace/buying/buying.json ${WORK_DIR}/apps/erpnext/erpnext/buying/workspace/buying/buying.json
COPY patches/workspace/crm/crm.json ${WORK_DIR}/apps/erpnext/erpnext/crm/workspace/crm/crm.json
COPY patches/workspace/manufacturing/manufacturing.json ${WORK_DIR}/apps/erpnext/erpnext/manufacturing/workspace/manufacturing/manufacturing.json
COPY patches/workspace/selling/selling.json ${WORK_DIR}/apps/erpnext/erpnext/selling/workspace/selling/selling.json

COPY patches/data/industry_type.txt ${WORK_DIR}/apps/erpnext/erpnext/setup/setup_wizard/data/industry_type.txt
COPY patches/data/lead_source.txt ${WORK_DIR}/apps/erpnext/erpnext/setup/setup_wizard/data/lead_source.txt
COPY patches/data/uom_conversion_data.json ${WORK_DIR}/apps/erpnext/erpnext/setup/setup_wizard/data/uom_conversion_data.json
COPY patches/data/uom_data.json ${WORK_DIR}/apps/erpnext/erpnext/setup/setup_wizard/data/uom_data.json

CMD ["/bin/bash"]