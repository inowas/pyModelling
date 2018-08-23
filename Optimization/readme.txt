Optimization service for modflow and mt3d-usgs models.

Start command: "python ./main.py"

The main.py creates a message consumer that listens to the optimization request queue "REQUEST_QUEUE".
When new optimization task is published, consumer creates worker containers, assigns tasks to them in detached mode and continues consuming.
When the job is finished containers are stopped automatically.

Example input can be found in ./tests.


Requirements for the main process:
- Python version >= 3.5
- Docker version >= 18
- Python libraries: pika==0.12.0, docker==3.4.1

Requirements for the Optimization container (./Optimization/Dockerfile):
- Python version >= 3.5
- Python libraries:
    scipy==1.1.0
    flopy==3.2.9
    pika==0.12.0
    mystic==0.3.1
    numpy==1.12.0
    scikit-learn==0.19.1
    deap==1.2.2

Requirements for the Simulation container (./Simulation/Dockerfile):
- Python version >= 3.5
- Python libraries:
    scipy=1.1.0
    flopy==3.2.9
    numpy==1.12.0
    pika==0.12.0
- Executables:
    mf2005
    mfnwt
    mt3dusgs


A default configuration is defined in the ./config.json file.
All parameters can be overridden with environment variables with the same name, where:
    
    "HTTP_PROXY" and "HTTPS_PROXY": proxy ports if proxy server is used,
    "MODEL_FILE_NAME": name of optimization-model input file that will be created,
    "OPTIMIZATION_DATA_FOLDER_AT_HOST": folder on the host to which temporary model files will be written,
    "OPTIMIZATION_DATA_FOLDER_IN_CONTAINER": folder in the docker containers to which temporary model files will be written,
    "RABBITMQ_HOST": rabbitmq server host,
    "RABBITMQ_PORT": rabbitmq server port,
    "RABBITMQ_VIRTUAL_HOST": rabbitmq server virtual host,
    "RABBITMQ_USER": rabbitmq server username,
    "RABBITMQ_PASSWORD": rabbitmq server password,
    "OPTIMIZATION_REQUEST_QUEUE": name of the queue that service is listening to,
    "OPTIMIZATION_RESPONSE_QUEUE": name of the queue to which results will be published,
    "SIMULATION_REQUEST_QUEUE": name of the simulation jobs request queue (used only internally, created by the service and deleted after the optimization is finished),
    "SIMULATION_RESPONSE_QUEUE": name of the simulation jobs results queue (used only internally, created by the service and deleted after the optimization is finished),
    "NUM_SOLVERS_GA": number of simulation worker containers that will be created for each new optimization task by default,
    "OPTIMIZATION_IMAGE": name of the optimization docker image (docker file can be found in ./Optimization),
    "SIMULATION_IMAGE": name of the simulation docker image (docker file can be found in ./Simulation)