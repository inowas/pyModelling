import os
import sys
import pika
import json
import uuid

from DockerManager import DockerManager


class Server(object):
    host_temp_folder = './optimization_temp_data'
    solvers_per_ga_job = 2
    solvers_per_simplex_job = 1
    configuration = {
        'TEMP_FOLDER': './optimization_temp_data',
        'CONFIG_FILE_NAME': 'config.json',
        'HOST': 'sheep.rmq.cloudamqp.com',
        'PORT': '5672',
        'VIRTUAL_HOST': 'ylfqreqi',
        'USER': 'ylfqreqi',
        'PASSWORD': 'oe3Hqc_nPWomlp2eDnq5Chwtnfy3jnBk',
        'REQUEST_QUEUE': 'optimization_request_queue',
        'RESPONSE_QUEUE': 'optimization_response_queue',
        'SIMULATION_REQUEST_QUEUE': 'simulation_request_queue',
        'SIMULATION_RESPONSE_QUEUE': 'simulation_response_queue',
    }
    def __init__(self):
        self.docker_manager = DockerManager(self.configuration)
        self.request_channel = None
        self.response_channel = None
    
    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.configuration['HOST'],
                port=int(self.configuration['PORT']),
                virtual_host=self.configuration['VIRTUAL_HOST'],
                credentials=pika.PlainCredentials(
                    self.configuration['USER'], self.configuration['PASSWORD']
                ),
                heartbeat_interval=0
            )
        )

        self.read_channel = self.connection.channel()
        self.read_channel.queue_declare(
            queue=self.configuration['REQUEST_QUEUE'],
            durable=True
        )
        
        self.response_channel = self.connection.channel()
        self.response_channel.queue_declare(
            queue=self.configuration['RESPONSE_QUEUE'], 
            durable=True
        )
    
    def send_message(self, message):
        response = json.dumps(message).encode()
        self.response_channel.basic_publish(
            exchange='',
            routing_key=self.configuration['RESPONSE_QUEUE'],
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
    
    def consume(self):
        self.read_channel.basic_consume(
            self.on_request, queue=self.configuration['REQUEST_QUEUE']
        )
        print(" [x] Optimization server awaiting requests")
        self.read_channel.start_consuming()
    
    def on_request(self, channel, method, properties, body):
        print(' [.] Deleting inactive containers...')
        self.docker_manager.remove_exited_containers()

        content = json.loads(body.decode())

        optimization_id = str(uuid.uuid4())
        self.configuration['OPTIMIZATION_ID'] = optimization_id
        
        solvers_per_job = self.solvers_per_simplex_job
        if content['optimization']['parameters']['method'] == 'GA':
            solvers_per_job = self.solvers_per_ga_job
        

        data_dir = os.path.join(
            os.path.realpath(self.host_temp_folder),
            str(optimization_id)
        )
        config_file = os.path.join(
            data_dir,
            self.configuration['CONFIG_FILE_NAME']
        )

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        with open(config_file, 'w') as f:
            json.dump(content, f)

        print(' [.] Accepted Optimization request. \
        Starting 1 Optimization and {} Simulation containers.'\
        .format(solvers_per_job))
    
        self.send_message(
            {
                'status_code': "202",
                'message': 'Request accepted. \
                Starting 1 Optimization manager and {} solvers.'\
                .format(
                    solvers_per_job
                )
            }
        )
        
        self.docker_manager.run_simulation_container(
            number=solvers_per_job
        )
         
        
        self.docker_manager.run_optimization_container(
            number=1
        )
        print(' [.] Started 1 Optimization and {} Simulation containers'\
        .format(solvers_per_job))

        channel.basic_ack(delivery_tag = method.delivery_tag)
        print(" [x] Optimization server awaiting requests")
    
    # def clean(self):
    #     print(" [-] Stopping simulation server")
    #     self.connection.close()



if __name__ == "__main__":
    server = Server()
    server.connect()
    server.consume()
    # try:
    #     server.consume()
    # except KeyboardInterrupt:
    #     server.clean()
    #     try:
    #         sys.exit(0)
    #     except SystemExit:
    #         os._exit(0)


