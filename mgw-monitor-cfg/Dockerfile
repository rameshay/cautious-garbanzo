#FROM ubuntu:16.04
FROM python:2.7
MAINTAINER Ramesh Ayyagari

ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
COPY files/update-db.py  /root/update-db.py
RUN chmod +x /root/update-db.py
COPY files/cfg.json  /root/db.json
RUN chmod 666 /root/db.json
COPY files/docker-entry-point.sh /root/docker-entry-point.sh
RUN chmod +x /root/docker-entry-point.sh
ENTRYPOINT ["/root/docker-entry-point.sh"]
