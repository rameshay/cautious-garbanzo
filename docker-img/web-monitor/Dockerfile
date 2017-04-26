FROM ubuntu:16.04
MAINTAINER Ramesh Ayyagari "ramesh_ayyagari@symantec.com"

RUN apt-get update; apt-get install -y nginx
RUN echo 'Hi, I am in your container' \
> /var/www/html/index.html
RUN apt-get update && apt-get install -y openssh-server apache2 supervisor
RUN mkdir -p /var/lock/apache2 /var/run/apache2 /var/run/sshd /var/log/supervisor
COPY supervisor.conf /etc/supervisor/conf.d/supervisord.conf
EXPOSE 22 80
CMD ["/usr/bin/supervisord"]

