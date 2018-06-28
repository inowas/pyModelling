import os
import sys
import pika
import warnings
import json

from Optimization import Optimization

DATA_FOLDER = sys.argv[1]
HOST = sys.argv[2]
PORT = sys.argv[3]
VIRTUAL_HOST = sys.argv[4]
USER = sys.argv[5]
PASSWORD = sys.argv[6]
REQUEST_QUEUE = sys.argv[7]
RESPONSE_QUEUE = sys.argv[8]

warnings.filterwarnings("ignore")
CONNECTION = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=HOST,
        port=int(PORT),
        virtual_host=VIRTUAL_HOST,
        credentials=pika.PlainCredentials(USER, PASSWORD),
        heartbeat_interval=0
    ))

def on_request(ch, method, props, body):

    content = json.loads(body.decode("utf-8"))
    ch.basic_ack(delivery_tag=method.delivery_tag)

    print('Summary of the optimization problem:')
    print('Author: %s' % content.get("author"))
    print('Project: %s' % content.get("project"))
    print('Model Id: %s' % content.get("model_id"))
    print('Type: %s' % content.get("type"))
    print('Version: %s' % content.get("version"))

    response_channel = CONNECTION.channel()
    response_channel.queue_declare(queue=RESPONSE_QUEUE, durable=True)

    optimization = Optimization(
        request_data=content,
        response_channel=response_channel,
        response_queue=RESPONSE_QUEUE,
        data_folder=DATA_FOLDER,
        rabbit_host=HOST, 
        rabbit_port=PORT,
        rabbit_vhost=VIRTUAL_HOST,
        rabbit_user=USER,
        rabbit_password=PASSWORD
    )
    optimization.run_optimization()


if __name__ == "__main__":

    read_channel = CONNECTION.channel()
    read_channel.queue_declare(queue=REQUEST_QUEUE, durable=True)

    read_channel.basic_qos(prefetch_count=1)
    read_channel.basic_consume(on_request, queue=REQUEST_QUEUE)

    print(" [x] Optimization server awaiting requests")
    read_channel.start_consuming()


