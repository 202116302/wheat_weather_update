FROM python:3

WORKDIR /usr/src/app


## Copy all src files

COPY wheat_dashboard_iksan /usr/src/app


## Install packages

RUN pip install -r requirements.txt

