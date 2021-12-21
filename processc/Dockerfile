FROM python
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>

# install deps
RUN pip install pygcdm pyyaml aiohttp
RUN apt-get update
RUN apt-get install -y iputils-ping iproute2 vim

# copy in config
COPY /server/* /server/

# copy in custom user scripts
COPY /usr/* /server/
