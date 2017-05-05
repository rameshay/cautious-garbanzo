#!/bin/sh

if [ -f /var/tmp/db.json ]
then
    echo "Found db file processing it next"
    /usr/local/bin/update-db.py -f /var/tmp/db.json
else
    ls /var/tmp
    exit -1
fi

