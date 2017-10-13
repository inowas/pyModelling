#!/usr/bin/env python

import json
import os
import pika
import sys
import traceback
import warnings
from InowasFlopyAdapter.InowasFlopyReadAdapter import InowasFlopyReadAdapter

print(sys.argv)

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

print(datafolder)


def process(content):
    calculation_id = content.get("calculation_id")
    m_type = content.get("type")
    version = content.get("version")

    print('Summary:')
    print('Calculation Id: %s' % calculation_id)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'flopy_read_data':
        print('Read flopy data:')
        project_folder = os.path.join(datafolder, calculation_id)
        print('Project folder: ' + str(project_folder))
        print('Request: ' + str(content.get("request")))

        try:
            flopy = InowasFlopyReadAdapter(version, project_folder, content.get("request"))
            return flopy.response()
        except:
            return dict(
                status_code=500,
                message=traceback.format_exc()
            )

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
                     body=json.dumps(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue=sys.argv[7])

print(" [x] Awaiting RPC requests")
channel.start_consuming()
