FROM python
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>

# install deps
RUN pip install pygcdm pyyaml aiohttp
RUN apt-get update
RUN apt-get install -y iputils-ping iproute2 vim

# create custom conda environment for user
RUN mkdir -p /root/tmp \
    && cd /root/tmp \
    && curl -O https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh \
    && bash Anaconda3-2021.05-Linux-x86_64.sh -b -p /root/anaconda3 

# copy in config
COPY /server/* /server/

# copy in custom user scripts
COPY /usr/* /server/

# run custom user script
RUN chmod -v 755 server/custom_processc_script.sh
RUN /bin/bash server/custom_processc_script.sh

# need to init conda then "bounce shell" for it to take effect before creating env
RUN echo 'export PATH=/root/anaconda3/condabin:$PATH' >> /root/.bashrc
RUN echo 'export PATH=/root/anaconda3/bin:$PATH' >> /root/.bashrc
RUN . /root/.bashrc \
    && conda init bash

# install a conda environment from user defined file
RUN . /root/.bashrc \
    && conda env create -f /server/environment.yml \

