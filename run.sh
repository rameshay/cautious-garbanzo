#!/bin/sh
sudo docker rm syslog
sudo docker rm redis
sudo docker rm mgw-monitor

sudo docker run -d --name syslog helder/rsyslog
sudo docker run --name local-redis --link syslog -v /tmp/redis-data:/data -d redis redis-server --appendonly yes
sudo docker run -d --name eoe-pdx-mobile-gateway-034d61437ed2a4899 --hostname eoe-pdx-mobile-gateway-034d61437ed2a4899 --link syslog --privileged -v /tmp/eoe-pdx-mobile-gateway-034d61437ed2a4899:/var/ mgw-monitor:1.0 
