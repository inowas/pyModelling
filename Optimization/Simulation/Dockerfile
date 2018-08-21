FROM python:3.6-jessie

COPY ../Simulation /Simulation
COPY ../../bin/linux/* /usr/local/bin/

RUN pip install numpy==1.12.0
RUN pip install -r /Simulation/requirements.txt

CMD python /Simulation/SimulationServer.py
