FROM ubuntu:20.04

MAINTAINER Ian Czekala "iancze@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev python3-venv git

RUN adduser maps

WORKDIR /home/maps

COPY requirements.txt requirements.txt
RUN python3 -m venv venv

# copy the application files to the container 
COPY application application
COPY maps.py boot.sh ./
RUN chmod +x boot.sh

# install the application dependencies, which includes MAPSDB, into venv
RUN venv/bin/pip install wheel 
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

ENV FLASK_APP maps.py

# set all the files in the directory to the maps user
# and change to this user
RUN chown -R maps:maps ./
USER maps

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]