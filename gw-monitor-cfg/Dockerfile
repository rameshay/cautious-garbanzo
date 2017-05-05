FROM mgw-monitor:1.0
MAINTAINER Ramesh Ayyagari

COPY files/update-db.py  /usr/local/bin/update-db.py
COPY files/cfg.json  /var/tmp/db.json
RUN chmod 666 /var/tmp/db.json
RUN chmod +x /usr/local/bin/update-db.py
COPY files/docker-entry-point.sh /root/docker-entry-point.sh
RUN chmod +x /root/docker-entry-point.sh
ENTRYPOINT ["/root/docker-entry-point.sh"]
