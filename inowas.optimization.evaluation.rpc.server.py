#!/usr/bin/env python

import json
import os
import shutil
import sys
import asyncio
from functools import partial
from aio_pika import connect, IncomingMessage, Exchange, Message

from InowasFlopyAdapter.InowasFlopyReadFitness import InowasFlopyReadFitness
from InowasFlopyAdapter.InowasFlopyCalculationAdapter import InowasFlopyCalculationAdapter

DATA_FOLDER = sys.argv[1]
HOST = sys.argv[2]
PORT = sys.argv[3]
VIRTUAL_HOST = sys.argv[4]
USER = sys.argv[5]
PASSWORD = sys.argv[6]
QUEUE = sys.argv[7]

datafolder = os.path.realpath(DATA_FOLDER)
scriptfolder = os.path.dirname(os.path.realpath(__file__))
binfolder = os.path.join(scriptfolder, 'bin')


def process(content):
    model_id = content.get("model_id")
    gen_id = content.get("gen_id")
    ind_id = content.get("ind_id")
    model_data = content.get("data")
    optimization_data = content.get("optimization")
    target_directory = os.path.join(datafolder, str(model_id)+str(gen_id)+str(ind_id))

    os.makedirs(target_directory)

    print("Running flopy calculation for model '{0}' generation '{1}' individual '{2}'".format(model_id, gen_id, ind_id))
    print('The target directory is %s' % target_directory)

    model_data['mf']['mf']['modelname'] = model_id
    model_data['mf']['mf']['model_ws'] = target_directory
    model_data['mf']['mf']['exe_name'] = os.path.join(binfolder, sys.platform, model_data['mf']['mf']['exe_name'])

    model_data['mt']['mt']['modelname'] = model_id
    model_data['mt']['mt']['model_ws'] = target_directory
    model_data['mt']['mt']['exe_name'] = os.path.join(binfolder, sys.platform, model_data['mt']['mt']['exe_name'])

    try:
        flopy_adapter = InowasFlopyCalculationAdapter(version, model_data, 'candidate_model')
        fitness = InowasFlopyReadFitness(optimization_data, flopy_adapter).get_fitness()

        response = {
            'status_code': "200",
            'fitness': fitness
        }

    except:
        response = {
            'status_code': "500",
            'fitness': [i["penalty_value"] for i in optimization_data["objectives"]]
        }

    print('Deleting the target directory %s' % target_directory)
    shutil.rmtree(target_directory) # deleting target directory

    return json.dumps(response)


async def on_request(exchange: Exchange, message: IncomingMessage):
    with message.process():
        content = json.loads(message.body.decode())
        response = process(content).encode()

        await exchange.publish(
            Message(
                body=response,
                correlation_id=message.correlation_id
            ),
            routing_key=message.reply_to
        )
        print('Request complete')


async def main(loop):
    # Perform connection
    connection = await connect(
        host=HOST,
        port=PORT,
        login=USER,
        password=PASSWORD,
        virtualhost=VIRTUAL_HOST,
        loop=loop
    )

    # Creating a channel
    channel = await connection.channel()

    # Declaring queue
    queue = await channel.declare_queue(QUEUE)

    # Start listening the queue with name
    await queue.consume(
        partial(
            on_request,
            channel.default_exchange
        )
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))

    # we enter a never-ending loop that waits for data
    # and runs callbacks whenever necessary.
    print(" [x] Evaluation server awaits RPC requests")
    loop.run_forever()