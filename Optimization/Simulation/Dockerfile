FROM inowas/pymodelling:modflow

COPY . /Simulation

RUN pip install numpy==1.12.0
RUN pip install -r /Simulation/requirements.txt

CMD python /Simulation/SimulationServer.py
