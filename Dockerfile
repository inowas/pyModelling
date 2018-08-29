FROM python:3.6-stretch

MAINTAINER Ralf Junghanns <ralf.junghanns@gmail.com>

RUN buildDeps="netcat unzip wget g++ gfortran make" && \
    apt-get update && \
    apt-get install -y $buildDeps --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY . /pymodelling
COPY ./bin/linux/* /usr/local/bin/

RUN pip install numpy==1.12.0
RUN pip install -r /pymodelling/requirements.txt

# Complie modflow-excecutables
RUN pip install https://github.com/modflowpy/pymake/zipball/master

WORKDIR /
RUN wget -O /pymake.zip https://github.com/modflowpy/pymake/archive/1.1.zip
RUN unzip /pymake.zip

WORKDIR /pymake-1.1
RUN for file in ./examples/*; do python3 $file 2>/dev/null; done
RUN mv ./temp/* /usr/local/bin

WORKDIR /pymodelling
