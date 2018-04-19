#!/usr/bin/env python

import json
import os
import pika
import sys
import traceback
import warnings
from .InowasFlopyReadFitness import InowasFlopyReadFitness


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
scriptfolder = os.path.dirname(os.path.realpath(__file__))
binfolder = os.path.join(scriptfolder, 'bin')


def process(content):
    author = content.get("author")
    project = content.get("project")
    calculation_id = content.get("calculation_id")
    model_id = content.get("model_id")
    m_type = content.get("type")
    version = content.get("version")
    data = content.get("data")
    fitness_data = content.get("fitness")

    print('Summary:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Model Id: %s' % model_id)
    print('Calculation Id: %s' % calculation_id)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'flopy_calculation_fitness' and fitness_data is not None:

        print("Running flopy calculation for model-id '{0}' with calculation-id '{1}'".format(model_id, calculation_id))
        target_directory = os.path.join(datafolder, calculation_id)
        print('The target directory is %s' % target_directory)

        print('Write config to %s' % os.path.join(target_directory, 'configuration.json'))
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        with open(os.path.join(target_directory, 'configuration.json'), 'w') as outfile:
            json.dump(content, outfile)

        data['mf']['mf']['modelname'] = calculation_id
        data['mf']['mf']['model_ws'] = target_directory
        data['mf']['mf']['exe_name'] = os.path.join(binfolder, sys.platform, data['mf']['mf']['exe_name'])

        try:
            flopy_adapter = InowasFlopyCalculationAdapter(version, data, calculation_id)
            fitness = InowasFlopyReadFitness(fitness_data, flopy_adapter).get_fitness()

            response = {
                response['status_code']: "200",
                response['model_id']: model_id,
                response['fitness']: fitness
            }

        except:
            response = {
                response['status_code']: "500",
                response['model_id']: model_id,
                response['fitness']: None
            }

    return json.dumps(response)


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
