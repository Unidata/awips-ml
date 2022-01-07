FROM centos:7
MAINTAINER "Rio McMahon" <rmcmahon@ucar.edu>
RUN yum -y update; yum clean all
RUN yum install httpd -y

ENV HOME /root
ENV WORKDIR /root

# install AWIPS pre-reqs
RUN yum -y install sudo wget perl less rsync vim

# do awips install
RUN wget https://www.unidata.ucar.edu/software/awips2/awips_install.sh \
    && chmod 755 awips_install.sh \
    && sudo ./awips_install.sh --edex

# install conda per https://phoenixnap.com/kb/how-to-install-anaconda-centos-7
# we do this as user `awips` since that is the user that calls EXEC
USER awips
ENV HOME /home/awips

RUN mkdir -p /home/awips/tmp \
    && cd /home/awips/tmp \
    && curl -O https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh \
    && bash Anaconda3-2021.05-Linux-x86_64.sh -b -p /home/awips/anaconda3 

# fix yum since awips install breaks it per
# https://www.unidata.ucar.edu/support/help/MailArchives/awips/msg00365.html
RUN echo 'export LD_LIBRARY_PATH=/usr/lib:/lib:/usr/lib64:/lib64' >> /home/awips/.bashrc

# need to init conda then "bounce shell" for it to take effect before creating env
RUN echo 'export PATH=/home/awips/anaconda3/condabin:$PATH' >> /home/awips/.bashrc
RUN echo 'export PATH=/home/awips/anaconda3/bin:$PATH' >> /home/awips/.bashrc
RUN . /home/awips/.bashrc \
    && conda init bash

# install a conda environment so we can get python3.9 executable
RUN . /home/awips/.bashrc \
    && conda create --name grpc_env -y python=3.9 \
    && conda activate grpc_env \
    && pip install grpcio \
    && pip install pygcdm \
    && pip install pyyaml \
    && pip install aiohttp 

# do this to invalidate build cache below this because of issue with EDEX not ingesting the same file
ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache 

# start doing stuff as root
USER root

# cleanup awips_install script
RUN rm awips_install.sh

# load in edex server stuff
COPY /server/* /server/

# copy in user defined stuff
COPY /usr/* /server/

# load in config files
COPY /edexc/etc/conf/ldmd.conf /awips2/ldm/etc/ldmd.conf
COPY /edexc/etc/conf/setup.env /awips2/edex/bin/setup.env
COPY /edexc/etc/conf/edexServiceList /etc/rc.d/init.d/edexServiceList
COPY /edexc/etc/conf/registry.xml /awips2/ldm/etc/registry.xml
COPY /edexc/etc/conf/pqact.conf /awips2/ldm/etc/pqact.conf
COPY /edexc/etc/conf/CMIDataDescription_ML.xml /awips2/edex/data/utility/common_static/base/satellite/goesr/descriptions/Sectorized_CMI/CMIDataDescription_ML.xml
COPY /edexc/etc/conf/goesrCMI-ImageryStyleRules.xml /awips2/edex/data/utility/common_static/base/styleRules/goesrCMI-ImageryStyleRules.xml

# remove some systemd stuff per https://hub.docker.com/_/centos/
ENV container docker
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*; \
rm -f /lib/systemd/system/serial-getty\@.service;
VOLUME [ "/sys/fs/cgroup" ]

# create empty network file
RUN touch /etc/sysconfig/network

# copy in custom service scripts (this will run on init)
#    edex_start.service: starts edex server on startup
#    listener_start.service: starts edex_container to handle pygcdm 
#       trigger on startup
#    logger_redirect.service: redirects listener_start output to PID 1 
#       so viewable in docker logs
RUN mkdir -p /etc/systemd/system/multi-user.target.wants/
COPY /edexc/etc/systemd/edex_start.service /etc/systemd/system/edex_start.service
COPY /edexc/etc/systemd/edex_start.service /etc/systemd/system/multi-user.target.wants/edex_start.service
COPY /edexc/etc/systemd/listener_start.service /etc/systemd/system/listener_start.service
COPY /edexc/etc/systemd/listener_start.service /etc/systemd/system/multi-user.target.wants/listener_start.service
COPY /edexc/etc/systemd/logger_redirect.service /etc/systemd/system/logger_redirect.service
COPY /edexc/etc/systemd/logger_redirect.service /etc/systemd/system/multi-user.target.wants/logger_redirect.service
COPY /edexc/etc/systemd/edex_start.sh /scripts/edex_start.sh
RUN chmod 755 /scripts/edex_start.sh
