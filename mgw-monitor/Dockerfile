#FROM ubuntu:16.04
FROM python:2.7
MAINTAINER Ramesh Ayyagari
EXPOSE 500/tcp 
EXPOSE 4500/udp
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y racoon ipsec-tools dnsutils iputils-ping python python-pip 
RUN pip install --upgrade pip
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
COPY racoon-client/racoon.conf /etc/racoon/racoon.conf
COPY racoon-client/certs/cacert.pem /etc/racoon/certs/cacert.pem
COPY racoon-client/certs/mgwhealthchecker.key /etc/racoon/certs/mgwhealthchecker.key
COPY racoon-client/certs/mgwhealthchecker.pem /etc/racoon/certs/mgwhealthchecker.pem
COPY racoon-client/scripts/phase1_up.sh /etc/racoon/scripts/phase1_up.sh
COPY racoon-client/scripts/phase1_down.sh /etc/racoon/scripts/phase1_down.sh
RUN  chmod +x /etc/racoon/scripts/*.sh
#ENTRYPOINT ["/root/docker-entry-point.sh"]
CMD ["/bin/bash", "./files/docker-entry-point.sh"]
