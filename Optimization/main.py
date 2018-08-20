import os
import sys
import pika
import json
import uuid
import shutil
from DockerManager import DockerManager


class Server(object):

    def __init__(self):
        try:
            with open('./config.json') as f:
                self.configuration = json.load(f)
        except:
            print('ERROR: Could not load configuration from ./config.json file')

        self.docker_manager = DockerManager(self.configuration)
        self.request_channel = None
        self.response_channel = None
    
    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.configuration['RABBITMQ_HOST'],
                port=int(self.configuration['RABBITMQ_PORT']),
                virtual_host=self.configuration['RABBITMQ_VIRTUAL_HOST'],
                credentials=pika.PlainCredentials(
                    self.configuration['RABBITMQ_USER'], self.configuration['RABBITMQ_PASSWORD']
                ),
                heartbeat_interval=0
            )
        )

        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=self.configuration['REQUEST_QUEUE'],
            durable=True
        )
        self.channel.queue_declare(
            queue=self.configuration['RESPONSE_QUEUE'], 
            durable=True
        )
    
    def send_response(self, success, optimization_id, message):
        status_code = "200" if success else "500"
        response = json.dumps({
            'status_code': status_code,
            'message': message,
            'optimization_id': optimization_id
        }).encode()

        self.channel.basic_publish(
            exchange='',
            routing_key=self.configuration['RESPONSE_QUEUE'],
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
    
    def consume(self):
        self.channel.basic_consume(
            self.on_request, queue=self.configuration['REQUEST_QUEUE']
        )
        print(" [x] Optimization server awaiting requests")
        self.channel.start_consuming()
    
    def on_request(self, channel, method, properties, body):
        
        print(' [.] Deleting inactive containers...')
        self.docker_manager.remove_exited_containers()

        content = json.loads(body.decode())
        try:
            optimization_id=content['optimization_id']
        except KeyError:
            self.send_response(
                success=False,
                optimization_id=None,
                message="Error. Failed to read optimization ID"
            )
        print(' [.] Received {} request'.format(content['type']))
        if content['type'] == 'optimization_start':
            success, message = self.start_optimization(content)
            self.send_response(
                success=success,
                optimization_id=optimization_id,
                message=message
            )
        elif content['type'] == 'optimization_stop':
            success, message = self.stop_optimization(content['optimization_id'])
            self.send_response(
                success=success,
                optimization_id=optimization_id,
                message=message
            )
        else: 
            self.send_response(
                success=False,
                optimization_id=optimization_id,
                message='Error. Unknown requets type: {}'.format(content['type'])
            )

        channel.basic_ack(delivery_tag = method.delivery_tag)
        print(" [x] Optimization server awaiting requests")
        
        
    def start_optimization(self, content):
        try:
            optimization_id = str(content['optimization_id'])
        except Exception as e:
            message = "Error. Failed to read optimization ID. "+str(e)
            return False, message

        try:
            data_dir = os.path.join(
                os.path.realpath(self.configuration['HOST_TEMP_FOLDER']),
                optimization_id
            )
            config_file = os.path.join(
                data_dir,
                self.configuration['MODEL_FILE_NAME']
            )

            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            with open(config_file, 'w') as f:
                json.dump(content, f)
        except Exception as e:
            message = "Error. Could not write model configuration to {} . ".format(config_file)+str(e)
            return False, message
        try:
            solvers_per_job = 1
            if content['optimization']['parameters']['method'] == 'GA':
                solvers_per_job = self.configuration['NUM_SOLVERS_GA']
        except Exception as e:
            message = "Error. "+str(e)
            return False, message

        try: 
            self.docker_manager.run_container(
                container_type="optimization",
                job_id=optimization_id,
                number=1
            )
            print(' [.] Accepted Optimization request. Optimization container started')
            
            self.docker_manager.run_container(
                container_type="simulation",
                job_id=optimization_id,
                number=solvers_per_job
            )

            print(' [.] {} Simulation container(s) started'.format(solvers_per_job))
        except Exception as e:
            message = "Error. Failed to start workers. "+str(e)
            return False, message

        message = 'Successfully started 1 optimization and {} model solver containers.'\
        .format(
            solvers_per_job
        )

        return True, message

    def stop_optimization(self, optimization_id):
        try:
            print(' [.] Stopping containers...')
            self.docker_manager.stop_all_job_containers(
                job_id=optimization_id,
                remove=True
            )
        except Exception as e:
            message = "Warning. Could not stop workers. "+str(e)
            return True, message

        try:
            print(' [.] Deleting temporary files...')
            temp_optimization_folder = os.path.join(
                os.path.realpath(self.configuration['HOST_TEMP_FOLDER']),
                str(optimization_id)
            )
            shutil.rmtree(temp_optimization_folder)
        except Exception as e:
            message = "Warning. Could not delete temporary files in {}. "\
            .format(temp_optimization_folder)+str(e)
            return True, message
        
        try:
            print(' [.] Deleting simulation queues...')
            self.channel.queue_delete(
                queue=self.configuration['SIMULATION_REQUEST_QUEUE']+optimization_id
            )
            self.channel.queue_delete(
                queue=self.configuration['SIMULATION_RESPONSE_QUEUE']+optimization_id
            )
        
        except:
            message = "Warning. Could not delete simulation queues. "+str(e)
            return True, message
        
        message = 'Successfully terminated optimization.'
        return True, message

if __name__ == "__main__":
    server = Server()
    server.connect()
    server.consume()



