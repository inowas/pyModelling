#!/usr/bin/env python

import os
import sys
import pika
import json
import logging
import logging.config

from Simulation import Simulation


class SimulationServer(object):
    logger = logging.getLogger('simulation_server')

    def __init__(self):
        self.logger.info('### Initializing Simulation Server ###')
        self.logger.debug('Environment: ' + str(os.environ))

        self.optimization_id = os.environ['OPTIMIZATION_ID']
        self.simulation_request_queue = os.environ['SIMULATION_REQUEST_QUEUE']
        self.simulation_response_queue = os.environ['SIMULATION_RESPONSE_QUEUE']

        self.request_consumer_tag = 'simulation_request_consumer'

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.environ['RABBITMQ_HOST'],
                port=int(os.environ['RABBITMQ_PORT']),
                virtual_host=os.environ['RABBITMQ_VIRTUAL_HOST'],
                credentials=pika.PlainCredentials(os.environ['RABBITMQ_USER'], os.environ['RABBITMQ_PASSWORD'])
            )
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=self.simulation_request_queue,
            durable=True
        )
        self.channel.queue_declare(
            queue=self.simulation_response_queue,
            durable=True
        )

    def consume(self):
        self.channel.basic_consume(
            self.on_request, queue=self.simulation_request_queue,
            consumer_tag=self.request_consumer_tag
        )
        self.logger.info("Simulation server awaiting requests")
        self.channel.start_consuming()

    # noinspection PyUnusedLocal
    def on_request(self, channel, method, properties, body):
        channel.basic_ack(delivery_tag=method.delivery_tag)
        content = json.loads(body.decode("utf-8"))

        if 'time_to_die' in content and content['time_to_die'] == True:
            self.logger.info("Stopping simulation server")
            self.channel.basic_cancel(consumer_tag=self.request_consumer_tag)
            self.connection.close()
            sys.exit()

        ind_id = content['ind_id']
        objects_data = content['objects_data']
        simulation_id = content['simulation_id']

        try:
            simulation = Simulation(simulation_id=simulation_id)
            fitness = simulation.evaluate(objects_data)
            response = {
                'status_code': '200',
                'ind_id': ind_id,
                'fitness': fitness,
                'message': 'Successfully finished simulation task for optimization: {}, simulation: {}' \
                    .format(self.optimization_id, simulation_id),
            }

        except Exception as e:
            self.logger.error(str(e), exc_info=True)
            response = {
                'status_code': '500',
                'ind_id': ind_id,
                'fitness': None,
                'message': str(e),
            }

        response = json.dumps(response).encode()

        self.logger.info('Publishing result to the simulation response queue: {}' \
                         .format(self.simulation_response_queue))
        self.channel.basic_publish(
            exchange='',
            routing_key=self.simulation_response_queue,
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )


if __name__ == "__main__":
    
    try:
        with open(os.path.join(os.path.dirname(__file__), 'log_config.json'), 'rt') as f:
            log_config = json.load(f)

        log_file_name = os.path.join(
            os.path.realpath(os.environ['OPTIMIZATION_DATA_FOLDER']),
            os.environ['OPTIMIZATION_ID'],
            'optimization-'+os.environ['OPTIMIZATION_ID']+'.log'
        )
        log_config['handlers']['file_handler']['filename'] = log_file_name
        logging.config.dictConfig(log_config)
    except Exception:
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        )

    ss = SimulationServer()
    ss.connect()
    ss.consume()
