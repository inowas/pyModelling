#!/usr/bin/env python

import json
import os
import pika
import sys
import warnings

from InowasGeoProcessing.InowasGeoProcessing import InowasGeoProcessing

warnings.filterwarnings("ignore")
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=sys.argv[2],
        port=int(sys.argv[3]),
        virtual_host=sys.argv[4],
        credentials=pika.PlainCredentials(sys.argv[5], sys.argv[6]),
        heartbeat_interval=0
    )
)

channel = connection.channel()
channel.queue_declare(queue=sys.argv[7])
datafolder = os.path.realpath(sys.argv[1])


def process(content):
    m_type = content.get("type")
    data = content.get("data")
    result = False

    print('Summary:')
    print('Type: %s' % m_type)

    if m_type == 'geoProcessing':
        print('Running geoProcessing:')
        gp = InowasGeoProcessing(datafolder, data)
        result = gp.response()
        print('Finished ...')

    return result


def on_request(ch, method, props, body):
    content = json.loads(body.decode("utf-8"))
    response = process(content)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=json.dumps(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue=sys.argv[7])

print(" [x] Awaiting RPC requests")
channel.start_consuming()
