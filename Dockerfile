FROM python
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>

# install deps
RUN pip install pygcdm
RUN pip install pyyaml
RUN apt-get update
RUN apt-get install -y iputils-ping
RUN apt-get install -y iproute2
RUN apt-get install -y vim
COPY /etc/* /
COPY /etc/data/test.nc /data/test.nc
