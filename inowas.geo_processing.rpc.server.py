#!/usr/bin/env python

import json
import os
import pika
import sys
import traceback
import warnings

from InowasGeoProcessing.InowasGeoProcessing import InowasGeoProcessing

warnings.filterwarnings("ignore")


def get_config_parameter(name):
    if os.environ[name]:
        return os.environ[name]

    raise Exception('Parameter with name ' + name + ' not found in environment-variables.')


def process(content):
    m_type = content.get("type")
    data = content.get("data")
    result = False

    print('Summary:')
    print('Type: %s' % m_type)

    if m_type == 'geoProcessing':
        print('Running geoProcessing:')
        try:
            gp = InowasGeoProcessing(datafolder, data)
            result = gp.response()
            print('Finished ...')
        except:
            result = {'status_code': "500", 'message': traceback.format_exc()}
            result = json.dumps(result)
            print('Errored ...')
            print(traceback.format_exc())

    return result


def on_request(ch, method, props, body):
    content = json.loads(body.decode("utf-8"))
    response = process(content)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=json.dumps(response))
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
channel.queue_declare(queue=get_config_parameter('GEO_PROCESSING_QUEUE'))
datafolder = os.path.realpath(sys.argv[1])

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue=get_config_parameter('GEO_PROCESSING_QUEUE'))

print(" [x] Awaiting RPC requests")
channel.start_consuming()
