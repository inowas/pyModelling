FROM python:3.6-stretch

MAINTAINER Ralf Junghanns <ralf.junghanns@gmail.com>

RUN buildDeps="unzip wget g++ gfortran make" && \
    apt-get update && \
    apt-get install -y $buildDeps --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install numpy
RUN pip install numpy==1.12.0

# Complie modflow-excecutables
RUN pip install https://github.com/modflowpy/pymake/zipball/master

COPY pyMake-scripts /scripts

RUN pip install requests

WORKDIR /scripts
RUN for file in ./*; do python $file 2>/dev/null; done
RUN mv ./temp/* /usr/local/bin

WORKDIR /

RUN rm -rf /pymake-1.1
