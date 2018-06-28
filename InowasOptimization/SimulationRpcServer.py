#!/usr/bin/env python

import json
import os
import shutil
import sys
import asyncio
from functools import partial
from aio_pika import connect, IncomingMessage, Exchange, Message

from Simulation import Simulation


DATA_FOLDER = sys.argv[1]
HOST = sys.argv[2]
PORT = sys.argv[3]
VIRTUAL_HOST = sys.argv[4]
USER = sys.argv[5]
PASSWORD = sys.argv[6]


import asyncio
from aio_pika import connect_robust
from aio_pika.patterns import RPC
import time



def process(content):

    simulation_id = content['simulation_id']
    optimization_id = content['optimization_id']
    objects_data = content['objects_data']
    
    start = time.time()
    simulation = Simulation(
        data_folder = DATA_FOLDER,
        optimization_id = optimization_id,
        simulation_id = simulation_id
    )
    try:
        fitness = simulation.evaluate(objects_data)
        response = {
            'status_code': "200",
            'fitness': fitness
        }

    except:
        raise
        response = {
            'status_code': "500",
            'fitness': 'err'
        }
    # print(json.dumps(response))
    # return time.time()-start
    return response

async def main():
    connection = await connect_robust(
        host=HOST,
        port=int(PORT),
        login=USER,
        password=PASSWORD,
        virtualhost=VIRTUAL_HOST
    )

    # Creating channel
    channel = await connection.channel()

    rpc = await RPC.create(channel)
    await rpc.register('process', process, auto_delete=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()





# async def on_request(exchange: Exchange, message: IncomingMessage):
#     with message.process():
#         content = json.loads(message.body.decode())
#         response = process(content).encode()

#         await exchange.publish(
#             Message(
#                 body=response,
#                 correlation_id=message.correlation_id
#             ),
#             routing_key=message.reply_to
#         )
#         print('Request complete')


# async def main(loop):
#     # Perform connection
#     connection = await connect(
#         host=HOST,
#         port=PORT,
#         login=USER,
#         password=PASSWORD,
#         virtualhost=VIRTUAL_HOST,
#         loop=loop
#     )

#     # Creating a channel
#     channel = await connection.channel()

#     # Declaring queue
#     queue = await channel.declare_queue(QUEUE)

#     # Start listening the queue with name
#     await queue.consume(
#         partial(
#             on_request,
#             channel.default_exchange
#         )
#     )


# if __name__ == "__main__":

#     loop = asyncio.get_event_loop()
#     loop.create_task(main(loop))

#     # Entering a never-ending loop that waits for data
#     # and runs callbacks whenever necessary.
#     print(" [x] Simulation server awaits RPC requests")
#     loop.run_forever()