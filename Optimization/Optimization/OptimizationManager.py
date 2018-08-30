import os
import pika
import json
import shutil

from Optimization import NSGA, NelderMead


class OptimizationManager(object):
    def __init__(self):

        print(' ### Initializing Optimization Manager ###')
        print(' Environment: ', os.environ)

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.environ['RABBITMQ_HOST'],
                port=int(os.environ['RABBITMQ_PORT']),
                virtual_host=os.environ['RABBITMQ_VIRTUAL_HOST'],
                credentials=pika.PlainCredentials(
                    os.environ['RABBITMQ_USER'], os.environ['RABBITMQ_PASSWORD']
                ),
                heartbeat_interval=0
            )
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            os.environ['OPTIMIZATION_RESPONSE_QUEUE'],
            durable=True
        )
        self.algorithm = None

    def reply_error(self, exception):
        response = {
            'status_code': '500',
            'optimization_id': os.environ['OPTIMIZATION_ID'],
            'message': str(exception),
        }
    
        response = json.dumps(response).encode()

        self.channel.basic_publish(
            exchange='',
            routing_key=os.environ['OPTIMIZATION_RESPONSE_QUEUE'],
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
    
    def clean(self):
        try:
            print('Sending Stop commands to the workers...')
            self.channel.basic_publish(
                exchange='',
                routing_key=os.environ['SIMULATION_REQUEST_QUEUE'],
                body=json.dumps({"time_to_die": True}).encode(),
                properties=pika.BasicProperties(
                    delivery_mode=2
                )
            )
        except:
            pass
        try:
            print('Deleting simulation queues...')
            self.channel.queue_delete(
                queue=os.environ['SIMULATION_REQUEST_QUEUE']
            )
            self.channel.queue_delete(
                queue=os.environ['SIMULATION_RESPONSE_QUEUE']
            )

        except:
            pass

        try:
            print('Closing connection...')
            self.connection.close()
            self.algorithm.connection.close()
        except:
            pass

        # try:
        #     print('Deleting optimization temp folder...')
        #     shutil.rmtree(
        #         os.path.join(
        #             os.path.realpath(os.environ['OPTIMIZATION_DATA_FOLDER']),
        #             os.environ['OPTIMIZATION_ID']
        #         )
        #     )
        # except:
        #     pass

    def run(self):
        try:
            config_file = os.path.join(
                os.path.realpath(os.environ['OPTIMIZATION_DATA_FOLDER']),
                os.environ['OPTIMIZATION_ID'],
                os.environ['MODEL_FILE_NAME']
            )

            with open(config_file) as f:
                content = json.load(f)

            kwargs = {
                'optimization_id': os.environ['OPTIMIZATION_ID'],
                'request_data': content,
                'response_channel': self.channel,
                'response_queue': os.environ['OPTIMIZATION_RESPONSE_QUEUE'],
                'rabbit_host': os.environ['RABBITMQ_HOST'], 
                'rabbit_port': os.environ['RABBITMQ_PORT'],
                'rabbit_vhost': os.environ['RABBITMQ_VIRTUAL_HOST'],
                'rabbit_user': os.environ['RABBITMQ_USER'],
                'rabbit_password': os.environ['RABBITMQ_PASSWORD'],
                'simulation_request_queue': os.environ['SIMULATION_REQUEST_QUEUE'],
                'simulation_response_queue': os.environ['SIMULATION_RESPONSE_QUEUE']
            }

            if content['optimization']['parameters']['method'] == 'GA':
                self.algorithm = NSGA(
                    **kwargs
                )
            elif content['optimization']['parameters']['method'] == 'Simplex':
                self.algorithm = NelderMead(
                    **kwargs
                )
        except Exception as e:
            self.reply_error(e)
            self.clean()
            raise

        try:
            self.algorithm.run()        
        except Exception as e:
            self.reply_error(e)
        finally:
            self.clean()



if __name__ == "__main__":
    om = OptimizationManager()
    om.run()
