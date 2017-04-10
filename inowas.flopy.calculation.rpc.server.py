#!/usr/bin/env python

import json
import os
import sys
import pika
import warnings
from InowasFlopyAdapter.InowasFlopyAdapter import InowasFlopyAdapter


warnings.filterwarnings("ignore")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))

channel = connection.channel()
channel.queue_declare(queue='rpc_flopy_calculation_queue')
datafolder = os.path.realpath(sys.argv[1])

print(datafolder)


def process(content):
    author = content.get("author")
    project = content.get("project")
    uuid = content.get("id")
    m_type = content.get("type")
    version = content.get("version")
    data = content.get("data")

    result = False

    print('Summary:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Uuid: %s' % uuid)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'flopy':
        print('Running flopy:')
        target_directory = os.path.join(datafolder, uuid)
        print(target_directory)
        data['mf']['model_ws'] = target_directory
        flopy = InowasFlopyAdapter(version, data)
        result = flopy.response()

    return result


def on_request(ch, method, props, body):
    content = json.loads(body.decode("utf-8"))
    response = process(content)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='rpc_flopy_calculation_queue')

print(" [x] Awaiting RPC requests")
channel.start_consuming()
