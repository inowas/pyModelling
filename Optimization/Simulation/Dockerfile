FROM python:3.6-jessie

RUN buildDeps="git" && \
    apt-get update && \
    apt-get install -y $buildDeps --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /
RUN git clone  -b master --depth 1 https://github.com/inowas/pyModelling.git pymodelling
RUN cp /pymodelling/bin/linux/* /usr/local/bin/
RUN rm -rf pymodelling

COPY . /Simulation

RUN pip install numpy==1.12.0
RUN pip install -r /Simulation/requirements.txt

CMD python /Simulation/SimulationServer.py
