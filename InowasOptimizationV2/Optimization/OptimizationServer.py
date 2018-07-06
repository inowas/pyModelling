import os
import sys
import pika
import warnings
import json

from Optimization import NSGA, NelderMead


def run():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ['HOST'],
            port=int(os.environ['PORT']),
            virtual_host=os.environ['VIRTUAL_HOST'],
            credentials=pika.PlainCredentials(
                os.environ['USER'], os.environ['PASSWORD']
            ),
            heartbeat_interval=0
        )
    )
    response_channel = connection.channel()
    response_channel.queue_declare(
        os.environ['RESPONSE_QUEUE'],
        durable=True
    )

    config_file = os.environ['TEMP_FOLDER'], os.environ['OPTIMIZATION_ID']

    with open(config_file) as f:
        content = json.load(f)

    kwargs = {
        'request_data': content,
        'response_channel': response_channel,
        'response_queue': os.environ['RESPONSE_QUEUE'],
        'rabbit_host': os.environ['HOST'], 
        'rabbit_port': os.environ['PORT'],
        'rabbit_vhost': os.environ['VIRTUAL_HOST'],
        'rabbit_user': os.environ['USER'],
        'rabbit_password': os.environ['PASSWORD'],
        'simulation_request_queue': os.environ['SIMULATION_REQUEST_QUEUE'],
        'simulation_response_queue': os.environ['SIMULATION_RESPONSE_QUEUE']
    }

    try:
        if content['optimization']['parameters']['method'] == 'GA':
            optimization = NSGA(
                **kwargs
            )
        elif content['optimization']['parameters']['method'] == 'Simplex':
            optimization = NelderMead(
                **kwargs
            )
        optimization.run()
        optimization.clean()
        

    except Exception as e:
        response = {
            'status_code': "500",
            'solutions': None,
            'message': str(e),
            'final': True
        }
        
        response = json.dumps(response).encode()

        response_channel.basic_publish(
            exchange='',
            routing_key=os.environ['RESPONSE_QUEUE'],
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )


if __name__ == "__main__":
    run()


