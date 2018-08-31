FROM inowas/pymodelling:modflow

COPY . /Optimization

RUN pip install numpy==1.12.0
RUN pip install -r /Optimization/requirements.txt

CMD python /Optimization/OptimizationManager.py
