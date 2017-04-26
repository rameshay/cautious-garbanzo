FROM ubuntu:16.10
MAINTAINER Ramesh Ayyagari

EXPOSE 500/tcp 
EXPOSE 4500/udp

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y racoon ipsec-tools dnsutils curl iputils-ping dnsmasq monit
COPY files/racoon /etc/default/racoon
COPY racoon-client/racoon.conf /etc/racoon/racoon.conf
COPY racoon-client/certs/cacert.pem /etc/racoon/certs/cacert.pem
COPY racoon-client/certs/mgwhealthchecker.key /etc/racoon/certs/mgwhealthchecker.key
COPY racoon-client/certs/mgwhealthchecker.pem /etc/racoon/certs/mgwhealthchecker.pem
COPY racoon-client/scripts/phase1_up.sh /etc/racoon/scripts/phase1_up.sh
COPY racoon-client/scripts/phase1_down.sh /etc/racoon/scripts/phase1_down.sh
RUN  chmod +x /etc/racoon/scripts/*.sh
COPY files/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
RUN  mkdir /var/run/racoon
RUN chmod +x /docker-entrypoint.sh
#CMD ["/docker-entrypoint.sh"]
