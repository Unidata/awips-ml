FROM python
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>

# install deps
RUN pip install pygcdm pyyaml
RUN apt-get update
RUN apt-get install -y iputils-ping iproute2 vim

# copy in config
COPY /server/config.yaml /server/config.yaml
COPY /server/edex_container_server.py /server/edex_container_server.py
COPY /server/trigger.py /server/trigger.py
