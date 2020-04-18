FROM python:3.8-alpine

RUN adduser -D maps

WORKDIR /home/maps

COPY requirements.txt requirements.txt
RUN python -m venv venv

# copy the application files to the container 
COPY application application
COPY application.py config.py boot.sh ./
RUN chmod +x boot.sh

# install the application dependencies, which includes MAPSDB, into venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

ENV FLASK_APP application.py

# set all the files in the application directory to the maps user
RUN chown -R application:maps ./
USER maps

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]