FROM python:3.8
RUN apt-get update
RUN apt-get -y install pip
RUN apt-get -y install nano
RUN apt-get -y install iputils-ping
RUN pip install --upgrade pip

COPY Auto_GS .
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

EXPOSE 8000