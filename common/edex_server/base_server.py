import socket
import queue
from concurrent import futures
import asyncio

# define class stuff
class BaseServer():
    def __init__(self, rx_port, tx_port, network_alias):

        # define queue and socket stuff
        self.fp_queue = asyncio.Queue()
        self.rx_port, self.tx_port, self.network_alias = rx_port, tx_port, network_alias

    async def listener(self):
        server = await asyncio.start_server(
                self.handle_trigger, self.network_alias, self.rx_port)
        print(f"starting server on {self.network_alias}:{self.rx_port}")
        async with server:
            await server.serve_forever()

    async def handle_trigger(self, reader, writer):
        data = await reader.read()
        message = data.decode()
        print(message)
        await self.fp_queue.put(message)
    
    async def responder(self):
        while True:
            if self.fp_queue.empty():
                data = "empty"
            else:
                data = await self.fp_queue.get()
            await asyncio.sleep(1)
            print(f"data from queue = {data}")

# define functions that run server
async def run_server(server):
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
    s = BaseServer(8888, 6901, "127.0.0.1")
    asyncio.run(run_server(s))
