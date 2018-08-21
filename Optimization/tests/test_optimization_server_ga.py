import pika
import json
import uuid


with open('./input_optimization_ga.json') as f:
    data = json.load(f)

with open('../config.json') as f:
    config = json.load(f)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=config['RABBITMQ_HOST'],
        port=int(config['RABBITMQ_PORT']),
        credentials=pika.PlainCredentials(config['RABBITMQ_USER'], config['RABBITMQ_PASSWORD']),
        virtual_host=config['RABBITMQ_VIRTUAL_HOST']
    )
)

channel = connection.channel()
channel.basic_publish(
    exchange='',
    routing_key=config['OPTIMIZATION_REQUEST_QUEUE'],
    body=json.dumps(data).encode()
)

print(" [x] Sent Test Data")

channel.queue_declare(queue=config['OPTIMIZATION_RESPONSE_QUEUE'], durable=True)
print(" [.] Listening for response")

consumer_tag = str(uuid.uuid4())

def consumer_callback(channel, method, properties, body):
    print(" [.] Received response")
    content = json.loads(body.decode())
    print(content)
    channel.basic_ack(delivery_tag = method.delivery_tag)
    if 'progress' in content and content['progress']['final']:
        channel.basic_cancel(
            consumer_tag=consumer_tag
        )

channel.basic_consume(
    queue=config['OPTIMIZATION_RESPONSE_QUEUE'],
    consumer_callback=consumer_callback,
    consumer_tag=consumer_tag
)
channel.start_consuming()
connection.close()
