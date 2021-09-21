FROM python
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>

# install deps
RUN pip install pygcdm
RUN git clone https://github.com/rmcsqrd/pygcdm
RUN apt-get update
RUN apt-get install -y iputils-ping
RUN apt-get install -y iproute2
RUN apt-get install -y vim
RUN bash
