#!/usr/bin/env python

import sys
import os
import json
import numpy
import pika
import warnings
from InowasInterpolation import Gaussian
from InowasInterpolation import Mean

warnings.filterwarnings("ignore")


def get_config_parameter(name):
    if os.environ[name]:
        return os.environ[name]

    raise Exception('Parameter with name ' + name + ' not found in environment-variables.')


def process(content):
    author = content.get("author")
    project = content.get("project")
    m_type = content.get("type")
    version = content.get("version")
    data = content.get("data")
    result = False

    print('Summary:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'interpolation':
        if 'gaussian' in data['methods']:
            print('Running gaussian interpolation...')
            interpolation = Gaussian.Gaussian(data)
            result = interpolation.calculate()
            print('Finished ...')
            if isinstance(result, numpy.ndarray):
                return result.tolist()

        if 'mean' in data['methods']:
            print('Running mean interpolation...')
            interpolation = Mean.Mean(data)
            result = interpolation.calculate()
            print('Finished ... with result: %s' % result)
            return result

    return result


def on_request(ch, method, props, body):
    content = json.loads(body.decode("utf-8"))
    response = json.dumps(process(content))

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=get_config_parameter('RABBITMQ_HOST'),
        port=int(get_config_parameter('RABBITMQ_PORT')),
        virtual_host=get_config_parameter('RABBITMQ_VIRTUAL_HOST'),
        credentials=pika.PlainCredentials(
            get_config_parameter('RABBITMQ_USER'),
            get_config_parameter('RABBITMQ_PASSWORD')
        ),
        heartbeat_interval=0
    )
)

channel = connection.channel()
channel.queue_declare(queue=get_config_parameter('INTERPOLATION_QUEUE'))
datafolder = os.path.realpath(sys.argv[1])

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue=get_config_parameter('INTERPOLATION_QUEUE'))

print(" [x] Awaiting RPC requests")
channel.start_consuming()
