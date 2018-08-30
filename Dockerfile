FROM inowas/modflow:latest

MAINTAINER Ralf Junghanns <ralf.junghanns@gmail.com>

RUN buildDeps="netcat" && \
    apt-get update && \
    apt-get install -y $buildDeps --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY . /pymodelling

WORKDIR /pymodelling
