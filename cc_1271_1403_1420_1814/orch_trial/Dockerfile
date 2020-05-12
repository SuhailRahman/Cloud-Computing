FROM ubuntu:18.04
RUN apt-get update -y && \
   apt-get install -y python3-pip python3-dev

ENV TEAM_NAME=cc_1271_1403_1420_1814
RUN mkdir -p /code
COPY ./requirements.txt /code/requirements.txt
RUN pip3 install -r /code/requirements.txt
COPY . /code
WORKDIR /code
