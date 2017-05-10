#!/bin/sh
printenv
cat /etc/hosts
ping -c 1 db
if [ -f /root/db.json ]
then
    echo "Found db file processing it next"
    /root/update-db.py -f /root/db.json | logger -d -n mgw-monitor-syslog -s
else
    ls /root
    exit -1
fi

