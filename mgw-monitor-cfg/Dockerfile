FROM ubuntu:16.04
MAINTAINER Ramesh Ayyagari
EXPOSE 500/tcp 
EXPOSE 4500/udp
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y racoon ipsec-tools dnsutils curl iputils-ping python python-pip python-pycurl
RUN pip install redis

COPY files/update-db.py  /usr/local/bin/update-db.py
COPY files/cfg.json  /var/tmp/db.json
RUN chmod 666 /var/tmp/db.json
RUN chmod +x /usr/local/bin/update-db.py
COPY files/docker-entry-point.sh /root/docker-entry-point.sh
RUN chmod +x /root/docker-entry-point.sh
ENTRYPOINT ["/root/docker-entry-point.sh"]
