#!/bin/bash

echo Bi12345678! | sudo -S service nginx restart
sudo service ssh restart
nohup node /home/frappe/frappe-bench/apps/frappe/socketio.js &
/home/frappe/frappe-bench/env/bin/gunicorn \
  --chdir=/home/frappe/frappe-bench/sites \
  --bind=0.0.0.0:8000 \
  --threads=10 \
  --workers=3 \
  --worker-class=gthread \
  --timeout=120 \
  --preload \
  frappe.app:application