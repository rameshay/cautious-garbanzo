#!/bin/bash

# Start the first process
/usr/sbin/racoon -f /etc/racoon/racoon.conf -l /var/log/racoon.log

status=$?
if [ $status -ne 0  ]; then
    echo "Failed to start racoon : $status"
    exit $status
fi

# Start the second process
/root/gw-monitor.py &
status=$?
if [ $status -ne 0  ]; then
    echo "Failed to start monitor script: $status"
    exit $status
fi

# Naive check runs checks once a minute to see if either of the processes exited.
# This illustrates part of the heavy lifting you need to do if you want to run
# more than one service in a container. The container will exit with an error
# if it detects that either of the processes has exited.
while /bin/true; do
    PROCESS_1_STATUS=$(ps aux |grep -q racoon)
    PROCESS_2_STATUS=$(ps aux |grep -q monitor)
    if [ $PROCESS_1_STATUS || $PROCESS_2_STATUS  ]; then
        echo "One of the processes has already exited."
        exit -1
    fi
    sleep 60
done

