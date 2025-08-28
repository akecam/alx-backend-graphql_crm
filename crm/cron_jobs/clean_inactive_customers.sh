#!/bin/bash

if [[ -z "$1" ]];
then
    echo "USAGE: $0 <cron_file.py>"
else
    echo "$(date +'%H:%M:%S'): $(python manage.py $1)" >> /tmp/customer_cleanup_log.txt 2> /dev/null
fi
