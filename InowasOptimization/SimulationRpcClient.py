import json
import asyncio
import uuid
from aio_pika import connect, IncomingMessage, Message

class SimulationRpcClient:
    """
    Model evaluation RCP client. Sends multiple candidate models to the solver server
    asynchronously 
    """
    content_type = 'application/json'

    def __init__(self, loop=None, host="rabbitmq", port=5672, virtual_host= "/", user="guest",
                 password="guest", routing_key="evaluation_queue", exclusive=True):
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.futures = {}
        # self.loop = loop
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.user = user
        self.password = password
        self.routing_key = routing_key
        self.exclusive = exclusive

    async def connect(self):
        self.connection = await connect(
            host=self.host,
            port=self.port,
            login=self.user,
            password=self.password,
            virtualhost=self.virtual_host,
            # loop=self.loop
        )
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(
            exclusive=self.exclusive
        )
        await self.callback_queue.consume(self.on_response)

        return self

    def on_response(self, message: IncomingMessage):
        future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

    async def call(self, loop, request_data):
        correlation_id = str(uuid.uuid4()).encode()
        future = loop.create_future()

        self.futures[correlation_id] = future

        await self.channel.default_exchange.publish(
            Message(
                json.dumps(request_data, default=self.numpy_type_translate).encode(),
                content_type=self.content_type,
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=self.routing_key,
        )

        return await future

    @staticmethod
    def numpy_type_translate(obj):
        """Converts numpy object to json serializable"""
        try:
            return obj.item()
        except:
            raise TypeError('Object %s is not JSON serializable and not Numpy dtype' % type(obj))
