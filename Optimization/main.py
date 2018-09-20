#!/usr/bin/env python

import os
import pika
import json
import shutil
import logging
import logging.config
import time

from DockerManager import DockerManager
from Validator import validate_spd


class Server(object):
    logger = logging.getLogger('main')
    inspection_wait_time = 5

    def __init__(self):

        self.logger.info('Initialization...')
        config_from_file = False

        try:
            with open(os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    './config.json')
            ) as f:
                config_from_file = json.load(f)
            
            self.configuration = self.mergeConfigurationWithEnvVariables(config_from_file, os.environ)

        except:
            self.logger.error('ERROR: Could not load configuration from ./config.json file')

        self.logger.info('Configuration File: \r\n'+str(config_from_file))
        self.logger.info('Environment Variables: \r\n'+str(os.environ))
        self.logger.info('Merged Config Variables: \r\n'+str(self.configuration))

        self.docker_manager = DockerManager(self.configuration)
        self.request_channel = None
        self.response_channel = None

    # noinspection PyMethodMayBeStatic
    def mergeConfigurationWithEnvVariables(self, configuration, additional):
        for name in configuration:
            if name in os.environ:
                configuration[name] = os.environ[name]

        for name in additional:
            if name not in configuration:
                configuration[name] = additional[name]

        return configuration

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.configuration['RABBITMQ_HOST'],
                port=int(self.configuration['RABBITMQ_PORT']),
                virtual_host=self.configuration['RABBITMQ_VIRTUAL_HOST'],
                credentials=pika.PlainCredentials(
                    self.configuration['RABBITMQ_USER'],
                    self.configuration['RABBITMQ_PASSWORD']
                ),
                heartbeat_interval=0
            )
        )

        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=self.configuration['OPTIMIZATION_REQUEST_QUEUE'],
            durable=True
        )
        self.channel.queue_declare(
            queue=self.configuration['OPTIMIZATION_RESPONSE_QUEUE'],
            durable=True
        )

    def send_response(self, success, optimization_id, message, status_code=None):
        if status_code is None:
            status_code = "200" if success else "500"
        response = json.dumps({
            'status_code': status_code,
            'message': message,
            'optimization_id': optimization_id
        }).encode()

        self.channel.basic_publish(
            exchange='',
            routing_key=self.configuration['OPTIMIZATION_RESPONSE_QUEUE'],
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

    def consume(self):
        self.channel.basic_consume(
            self.on_request, queue=self.configuration['OPTIMIZATION_REQUEST_QUEUE']
        )
        self.logger.info("Optimization server awaiting requests")
        self.channel.start_consuming()

    # noinspection PyUnusedLocal
    def on_request(self, channel, method, properties, body):
        self.logger.info('Deleting inactive containers...')
        self.docker_manager.remove_exited_containers()

        content = json.loads(body.decode())
        content = validate_spd(content)
        optimization_id = content['optimization_id']
        self.logger.info('Received {} request. ID: {}'.format(content['type'], optimization_id))

        if content['type'] == 'optimization_start':
            self.send_response(
                success=True,
                optimization_id=optimization_id,
                message='Received "optimization_start" request. Staring workers...',
                status_code='202'
            )
            if optimization_id in self.docker_manager._running_containers:
                success, message = self.stop_optimization(content['optimization_id'])
                response_message = 'Optimization with id {} already in progress. Will be restarted'.format(optimization_id)+'\r\n'+message
                self.send_response(
                    success=success,
                    optimization_id=optimization_id,
                    message=response_message
                )
            
            success, message = self.start_optimization(content)

            if success == False:
                self.send_response(
                    success=success,
                    optimization_id=optimization_id,
                    message=message
                )
                self.stop_optimization(content['optimization_id'])

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
                message='Error. Unknown request type: {}'.format(content['type'])
            )

        channel.basic_ack(delivery_tag=method.delivery_tag)
        self.logger.info("Optimization server awaiting requests")

    def start_optimization(self, content):
        self.logger.info('Start Optimization')
        try:
            optimization_id = str(content['optimization_id'])
        except Exception as e:
            message = "Error. Failed to read optimization ID. " + str(e)
            self.logger.error(message)
            return False, message

        try:
            data_dir = os.path.join(self.configuration['OPTIMIZATION_DATA_FOLDER'], optimization_id)
            config_file = os.path.join(data_dir, self.configuration['MODEL_FILE_NAME'])

            self.logger.info('Data folder is {}'.format(data_dir))

            if not os.path.exists(data_dir):
                self.logger.info('Create data folder is {}'.format(data_dir))
                os.makedirs(data_dir)

            with open(config_file, 'w') as f:
                self.logger.info('Write configuration to {}'.format(config_file))
                json.dump(content, f)

        except Exception as e:
            message = "Error. Could not write model configuration to {} . ".format(config_file) + str(e)
            self.logger.error(message)
            return False, message

        try:
            solvers_per_job = 1
            if content['optimization']['parameters']['method'] == 'GA':
                solvers_per_job = int(self.configuration['NUM_SOLVERS_GA'])
        except Exception as e:
            message = "Error. " + str(e)
            self.logger.error(message)
            return False, message

        try:
            self.logger.info('Starting optimization container...')
            self.docker_manager.run_container(
                container_type="optimization",
                job_id=optimization_id,
                number=1
            )
            
            self.logger.info('Starting {} simulation container(s)...'.format(solvers_per_job))
            self.docker_manager.run_container(
                container_type="simulation",
                job_id=optimization_id,
                number=solvers_per_job
            )

        except Exception as e:
            message = "Error. Failed to start workers. " + str(e)
            self.logger.error(message)
            return False, message

        try:
            self.logger.info('Inspecting containers...')
            time.sleep(self.inspection_wait_time)
            exited_containers = self.docker_manager.inspect_containers(optimization_id)
            if len(exited_containers) > 0:
                for container_id, container_info in exited_containers.items():
                    self.logger.error('Container: {} exited. Optimization will be terminated'.format(container_id))
                    self.logger.error('Container logs: {}'.format(container_info['logs']))

                message = 'Failed to start containers: {}. Check logs for details'.format([i for i in exited_containers])
                
                return False, message

        except Exception as e:
            message = "Error. Failed to inspect containers. " + str(e)
            self.logger.error(message)
            return False, message

        return True, 'Successfully started workers'

    def stop_optimization(self, optimization_id):
        message = ""
        try:
            self.logger.info('Stopping containers...')
            not_stopped_containers = self.docker_manager.stop_all_job_containers(
                job_id=optimization_id,
                remove=True
            )
            if not_stopped_containers:
                message += "Warning. Could not stop some workers. " + str(not_stopped_containers) + "\r\n"
                self.logger.warning(message)

        except Exception as e:
            message += "Warning. Could not stop workers. " + str(e) + "\r\n"
            self.logger.warning(message)

        # try:
        #     print(' [.] Deleting temporary files...')
        #     temp_optimization_folder = os.path.join(
        #         os.path.realpath(self.configuration['OPTIMIZATION_DATA_FOLDER']),
        #         str(optimization_id)
        #     )
        #     shutil.rmtree(temp_optimization_folder)
        # except Exception as e:
        #     message += "Warning. Could not delete temporary files in {}. " \
        #                    .format(temp_optimization_folder) + str(e) + "\r\n"
        #     print(message)

        try:
            self.logger.info('Deleting simulation queues...')
            self.channel.queue_delete(
                queue=self.configuration['SIMULATION_REQUEST_QUEUE'] + optimization_id
            )
            self.channel.queue_delete(
                queue=self.configuration['SIMULATION_RESPONSE_QUEUE'] + optimization_id
            )

        except:
            message += "Warning. Could not delete simulation queues. " + str(e) + "\r\n"
            self.logger.warning(message)

        if message == "":
            message = 'Successfully terminated optimization.'

        return True, message


if __name__ == "__main__":
    try:
        with open(os.path.join(os.path.dirname(__file__), 'log_config.json'), 'rt') as f:
            log_config = json.load(f)

        log_file_name = os.path.join(
            os.path.realpath(os.environ['OPTIMIZATION_DATA_FOLDER']),
            'optimization.log'
        )
        log_config['handlers']['file_handler']['filename'] = log_file_name
        logging.config.dictConfig(log_config)
    except Exception:
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        )
    server = Server()
    server.connect()
    server.consume()
