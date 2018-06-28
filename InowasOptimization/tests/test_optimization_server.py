import pika
import json

with open('./test_data/opt_model_input.json') as f:
    data = json.load(f)


connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=pika.PlainCredentials('inowas_user', 'inowas_password'),
        virtual_host='inowas_vhost'
    )
)

channel = connection.channel()

channel.queue_declare(queue='optimization_request_queue', durable=True)

channel.basic_publish(exchange='',
                      routing_key='optimization_request_queue',
                      body=json.dumps(data))

print(" [x] Sent Test Data")
connection.close()