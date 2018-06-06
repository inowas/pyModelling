import sys
import os
import pika
import warnings
import json

from InowasOptimization.Optimization import Optimization

HOST = sys.argv[1]
PORT = sys.argv[2]
VIRTUAL_HOST = sys.argv[3]
USER = sys.argv[4]
PASSWORD = sys.argv[5]
REQUEST_QUEUE = sys.argv[6]
RESPONSE_QUEUE = sys.argv[7]

warnings.filterwarnings("ignore")
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=sys.argv[2],
        port=int(sys.argv[3]),
        virtual_host=sys.argv[4],
        credentials=pika.PlainCredentials(sys.argv[5], sys.argv[6]),
        heartbeat_interval=0
    ))
read_channel = connection.channel()
read_channel.queue_declare(queue=REQUEST_QUEUE, durable=True)

write_channel = connection.channel()
write_channel.queue_declare(queue=RESPONSE_QUEUE, durable=True)

def process(content):
    author = content.get("author")
    project = content.get("project")
    model_id = content.get("model_id")
    m_type = content.get("type")
    version = content.get("version")

    print('Summary of the optimization problem:')
    print('Author: %s' % author)
    print('Project: %s' % project)
    print('Model Id: %s' % model_id)
    print('Type: %s' % m_type)
    print('Version: %s' % version)

    if m_type == 'optimization':

        print("Running optimization for model-id '{0}'".format(model_id))

        try:
            optimization = Optimization(content)
            pop, logbook, hypervolume_log = optimization.nsga_hybrid()
            
            response = {}
            response['status_code'] = "200"
            response['model_id'] = model_id
            response['result'] = pop
            response['logbook'] = logbook
            response['progress'] = hypervolume_log
            return response
        except:
            response = {}
            response['status_code'] = "500"
            response['model_id'] = model_id
            return response

    return dict(
        status_code=500,
        model_id=model_id,
        message="Internal Server Error."
    )


def on_request(ch, method, props, body):
    content = json.loads(body.decode("utf-8"))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    response = json.dumps(process(content)).encode()

    write_channel.basic_publish(
        exchange='',
        routing_key=RESPONSE_QUEUE,
        body=response,
        properties=pika.BasicProperties(
            delivery_mode=2  # make message persistent
        ))

read_channel.basic_qos(prefetch_count=1)
read_channel.basic_consume(on_request, queue=REQUEST_QUEUE)

print(" [x] Optimization server awaiting requests")
read_channel.start_consuming()


