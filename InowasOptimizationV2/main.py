import os
import sys
import pika
import json
import uuid

from DockerManager import DockerManager

configuration = {
    'TEMP_FOLDER': './temp',
    'HOST': 'sheep.rmq.cloudamqp.com',
    'PORT': '5672',
    'VIRTUAL_HOST': 'ylfqreqi',
    'USER': 'ylfqreqi',
    'PASSWORD': 'oe3Hqc_nPWomlp2eDnq5Chwtnfy3jnBk',
    'REQUEST_QUEUE': 'optimization_request_queue',
    'RESPONSE_QUEUE': 'optimization_response_queue',
    'SIMULATION_REQUEST_QUEUE': 'simulation_request_queue',
    'SIMULATION_RESPONSE_QUEUE': 'simulation_response_queue'
}

class Server(object):
    simulation_workers_num = 2

    def __init__(self, configuration):
        self.configuration = configuration
        self.docker_manager = DockerManager(configuration)
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
        self.read_channel.queue_declare(queue=self.configuration['REQUEST_QUEUE'], durable=True)
        
        self.response_channel = self.connection.channel()
        self.response_channel.queue_declare(queue=self.configuration['RESPONSE_QUEUE'], durable=True)
    
    def send_message(self, message):
        message['sourse'] = 'manager'
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
        self.read_channel.basic_qos(prefetch_count=1)
        self.read_channel.basic_consume(
            self.on_request, queue=self.configuration['REQUEST_QUEUE']
        )
        print(" [x] Optimization server awaiting requests")
        self.read_channel.start_consuming()
    
    def on_request(self, channel, method, properties, body):
        content = json.loads(body.decode())

        optimization_id = uuid.uuid4()
        self.configuration['OPTIMIZATION_ID'] = optimization_id

        data_dir = os.path.join(
            os.path.realpath('./temp'),
            str(optimization_id)
        )
        config_file = os.path.join(
            data_dir,
            'config.json'
        )

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        with open(config_file, 'w') as f:
            json.dump(content, f)

        self.send_message(
            {
                'status_code': "202",
                'message': 'Request accepted. Optimization id: {}. Starting workers.'\
                .format(
                    optimization_id
                )
            }
        )
        
        self.docker_manager.run_simulation_container(
            count=self.simulation_workers_num,
            detached = True
        )
         
        self.send_message(
            {
                'status_code': "202",
                'message': 'Started {} Simulation workers.'\
                .format(
                    len(self.docker_manager.simulation_containers)
                )
            }
        )
        
        self.docker_manager.run_optimization_container(
            count=1,
            detached=False    
        )

        self.send_message(
            {
                'status_code': "200",
                'message': 'Finished optimization'
            }
        )
    


if __name__ == "__main__":
    server = Server(configuration=configuration)
    server.connect()
    server.consume()
     


