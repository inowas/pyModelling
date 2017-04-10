#!/usr/bin/env python

import json
import os
import sys
import pika
import warnings
from InowasFlopyAdapter.InowasFlopyReadAdapter import InowasFlopyReadAdapter


warnings.filterwarnings("ignore")
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))

channel = connection.channel()
channel.queue_declare(queue='rpc_flopy_read_data_queue')
datafolder = os.path.realpath(sys.argv[1])

print(datafolder)


def process(content):
    uuid = content.get("id")
    m_type = content.get("type")
    version = content.get("version")

    print('Summary:')
    print('Uuid: %s' % uuid)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'flopy_read_data':
        print('Read flopy data:')
        project_folder = os.path.join(datafolder, uuid)
        flopy = InowasFlopyReadAdapter(version, project_folder, content.get("request"))
        return flopy.response()

    return dict(
        status_code=500,
        message="Internal Server Error. Request data does not fit."
    )


def on_request(ch, method, props, body):
    content = json.loads(body.decode("utf-8"))
    response = process(content)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='rpc_flopy_read_data_queue')

print(" [x] Awaiting RPC requests")
channel.start_consuming()
