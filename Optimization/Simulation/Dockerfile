FROM python:3.6-jessie

RUN buildDeps="g++ gfortran wget unzip make" && \
    apt-get update && \
    apt-get install -y $buildDeps --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# installing pymake
RUN pip install https://github.com/modflowpy/pymake/zipball/master

#installing mf2005
RUN wget https://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.12.00/MF2005.1_12u.zip \
    && unzip MF2005.1_12u.zip \
    && rm MF2005.1_12u.zip \
    && python -m pymake.pymake ./MF2005.1_12u/src /usr/local/bin/mf2005

#installing mfnwt
RUN wget https://water.usgs.gov/ogw/modflow-nwt/MODFLOW-NWT_1.1.4.zip \
    && unzip MODFLOW-NWT_1.1.4.zip \
    && rm MODFLOW-NWT_1.1.4.zip \
    && python -m pymake.pymake ./MODFLOW-NWT_1.1.4/src /usr/local/bin/mfnwt

#installing mt3dusgs
RUN wget https://water.usgs.gov/ogw/mt3d-usgs/mt3d-usgs_1.0.zip \
    && unzip mt3d-usgs_1.0.zip \
    && rm mt3d-usgs_1.0.zip \
    && python -m pymake.pymake ./mt3d-usgs_Distribution/src /usr/local/bin/mt3dusgs

COPY . /Simulation

RUN pip install numpy==1.12.0
RUN pip install -r /Simulation/requirements.txt

CMD python /Simulation/SimulationServer.py


