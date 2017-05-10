#FROM ubuntu:16.04
FROM python:2.7
MAINTAINER Ramesh Ayyagari
EXPOSE 500/tcp 
EXPOSE 4500/udp
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y racoon ipsec-tools dnsutils curl iputils-ping python python-pip wget vim
RUN pip install --upgrade pip
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
RUN pip install -r requirements.txt
COPY racoon-client/racoon.conf /etc/racoon/racoon.conf
COPY racoon-client/certs/cacert.pem /etc/racoon/certs/cacert.pem
COPY racoon-client/certs/mgwhealthchecker.key /etc/racoon/certs/mgwhealthchecker.key
COPY racoon-client/certs/mgwhealthchecker.pem /etc/racoon/certs/mgwhealthchecker.pem
COPY racoon-client/scripts/phase1_up.sh /etc/racoon/scripts/phase1_up.sh
COPY racoon-client/scripts/phase1_down.sh /etc/racoon/scripts/phase1_down.sh
RUN  chmod +x /etc/racoon/scripts/*.sh
COPY files/gw-monitor.py /root/gw-monitor.py
RUN chmod +x /root/gw-monitor.py
COPY files/docker-entry-point.sh /root/docker-entry-point.sh
RUN chmod +x /root/docker-entry-point.sh
ENTRYPOINT ["/root/docker-entry-point.sh"]
