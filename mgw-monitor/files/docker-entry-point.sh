#!/bin/bash

# Start the first process
if [ ! -d /var/log ]; then
    mkdir /var/log
fi
if [ ! -d /var/run ] ; then
    mkdir /var/run
fi

/usr/sbin/racoon -f /etc/racoon/racoon.conf  | logger -d -n mgw-monitor-syslog -s &

status=$?
if [ $status -ne 0  ]; then
    echo "Failed to start racoon : $status"
    exit $status
fi

# Start the second process
# Keep it in foreground. So that when this exists we restart the container
#/usr/bin/env python /code/files/gw-monitor.py | logger -d -n mgw-monitor-syslog -s 
#status=$?
#if [ $status -ne 0  ]; then
#    echo "Failed to start monitor script: $status"
#    exit $status
#fi

# Naive check runs checks once a minute to see if either of the processes exited.
# This illustrates part of the heavy lifting you need to do if you want to run
# more than one service in a container. The container will exit with an error
# if it detects that either of the processes has exited.
while [ true ] ; do
#    P1=$(ps aux |grep -q racoon)
#    P2=$(ps aux |grep -q monitor)
#    if [ -z "$P1" ] || [ -z "$P2" ]; then
#        echo "One of the processes has already exited."
#        exit 1
#    fi
    sleep 60
done
