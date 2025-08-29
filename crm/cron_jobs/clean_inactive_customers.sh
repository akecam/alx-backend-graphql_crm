#!/bin/bash

# Navigate to the Django project root
cd /home/donald/Documents/ALX/alx-backend-graphql_crm

# Get the current date in YYYY-MM-DD format
CURRENT_DATE=$(date +%Y-%m-%d)

# Calculate the date one year ago
ONE_YEAR_AGO=$(date -d "1 year ago" +%Y-%m-%d)

# Execute Django shell command to delete inactive customers
# and capture the number of deleted customers
DELETED_COUNT=$(python manage.py shell -c "
from datetime import datetime, timedelta
from django.utils import timezone
from crm.models import Customer, Order

one_year_ago = timezone.now() - timedelta(days=365)
inactive_customers_ids = Customer.objects.exclude(
    id__in=Order.objects.filter(order_date__gte=one_year_ago).values_list('customer', flat=True)
).values_list('id', flat=True)

deleted_count, _ = Customer.objects.filter(id__in=inactive_customers_ids).delete()
print(deleted_count)
")

# Log the number of deleted customers with a timestamp
echo "[${CURRENT_DATE}] Deleted ${DELETED_COUNT} inactive customers." >> /tmp/customer_cleanup_log.txt
