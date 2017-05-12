FROM python:2.7
MAINTAINER Ramesh Ayyagari
EXPOSE 443/tcp 
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
