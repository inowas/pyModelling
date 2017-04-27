#!/usr/bin/env python

import json
import os
import sys
import pika
import warnings
from InowasFlopyAdapter.InowasFlopyCalculationAdapter import InowasFlopyCalculationAdapter


warnings.filterwarnings("ignore")
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat_interval=0))
read_channel = connection.channel()
read_channel.queue_declare(queue='flopy_calculation_queue', durable=True)

write_channel = connection.channel()
write_channel.queue_declare(queue='flopy_calculation_finished_queue', durable=True)

datafolder = os.path.realpath(sys.argv[1])

scriptfolder = os.path.dirname(os.path.realpath(__file__))
binfolder = os.path.join(scriptfolder, 'bin')


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

    if m_type == 'flopy_calculation':
        print('Running flopy calculation with id %s' % uuid)

        target_directory = os.path.join(datafolder, uuid)
        print('The target directory is %s' % target_directory)

        print('Write config to %s' % os.path.join(target_directory, 'configuration.json'))
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        with open(os.path.join(target_directory, 'configuration.json'), 'w') as outfile:
            json.dump(content, outfile)

        data['mf']['model_ws'] = target_directory
        data['mf']['exe_name'] = os.path.join(binfolder, sys.platform, data['mf']['exe_name'])
        flopy = InowasFlopyCalculationAdapter(version, data, uuid)
        result = flopy.response()

    return result


def on_request(ch, method, props, body):
    content = json.loads(body.decode("utf-8"))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    response = process(content)
    response = str(response).replace('\'', '"')

    write_channel.basic_publish(
        exchange='',
        routing_key='flopy_calculation_finished_queue',
        body=response,
        properties=pika.BasicProperties(
            delivery_mode=2  # make message persistent
        ))

read_channel.basic_qos(prefetch_count=1)
read_channel.basic_consume(on_request, queue='flopy_calculation_queue')

print(" [x] Awaiting RPC requests")
read_channel.start_consuming()
