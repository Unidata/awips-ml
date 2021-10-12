import socket
import queue
from concurrent import futures
import asyncio
import sys
import yaml

# define class stuff
class BaseServer():
    def __init__(self, fp_queue,
            rx_port=None,
            tx_port=None,
            host=None,
            rx_port_trigger=None,
            pygcdm_client=None,
            pygcdm_server=None,
            ):

        # define queue and socket stuff
        self.fp_queue = fp_queue
        self.rx_port = rx_port
        self.tx_port = tx_port
        self.host = host
        self.rx_port_trigger = rx_port_trigger
        self.pygcdm_client = pygcdm_client
        self.pygcdm_server = pygcdm_server

    async def listener(self):
        server = await asyncio.start_server(
                self.handle_trigger, self.host, self.rx_port_trigger)
        print(f"starting server on {self.host}:{self.rx_port}")
        async with server:
            await server.serve_forever()

    async def handle_trigger(self, reader, writer):
        data = await reader.read()
        message = data.decode()
        await self.fp_queue.put(message)
    
    async def responder(self):
        while True:
            try:
                data = self.fp_queue.get_nowait()
            except asyncio.QueueEmpty:
                data = await self.fp_queue.get()
            print(data)

# define functions that run server
async def run_server(configs):
    server = BaseServer(asyncio.Queue(), **configs)
    g = await asyncio.gather(server.listener(), server.responder())


# inherit class stuff for preprocess or edex server

"""
EVENT LOOP:
Server waits for job to enter queue
if queue is empty:
        pass
if queue is not empty:
        take item from queue and request file from server
        do something with file (either process via TF or ingest into EDEX) <- "something" lives in subclass
"""

if __name__=="__main__":
    handler_type = sys.argv[1]
    with open("scripts/config.yaml") as file:
        config_dict = yaml.load(file, Loader=yaml.FullLoader)
    try:
        assert handler_type in ["tf_container", "edex_container"]
    except AssertionError:
        raise SyntaxError("incorrect input argument; options are \"tf_container\" or \"edex_container\"")
    asyncio.run(run_server(config_dict[handler_type]))


