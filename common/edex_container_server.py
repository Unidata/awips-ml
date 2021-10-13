import grpc
from pygcdm.netcdf_encode import netCDF_Encode
from pygcdm.netcdf_decode import netCDF_Decode
from pygcdm.protogen import gcdm_server_pb2_grpc as grpc_server
from pygcdm.protogen import gcdm_netcdf_pb2 as grpc_msg
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
        self.variable_spec = 'Sectorized_CMI' # BONE, need to expose this in an API


        # setup pygcdm stuff
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_server.add_GcdmServicer_to_server(Responder(), self.server)
        self.server.add_insecure_port(f'{self.pygcdm_client}:{self.rx_port}')
        self.request_handler = Requester(self.pygcdm_server, self.tx_port, self.variable_spec)

    async def listener(self):
        server = await asyncio.start_server(
                self.handle_trigger, self.host, self.rx_port_trigger)
        print(f"starting server on {self.host}:{self.rx_port_trigger}")
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
            print(f"file ready = {data}")
            print(f"queue size = {self.fp_queue.qsize()}\n")


class Responder(grpc_server.GcdmServicer):

    def __init__(self):
        self.encoder = netCDF_Encode()

    def GetNetcdfHeader(self, request, context):
        print('Header Requested')
        return self.encoder.generate_header_from_request(request)

    def GetNetcdfData(self, request, context):
        print('Data Requested')

        # stream the data response
        data_response = [self.encoder.generate_data_from_request(request)]
        for data in data_response:
            yield(data)

class Requester():
    def __init__(self, host, port, var_spec):
        self.host = host
        self.port = port
        self.variable_spec = var_spec

    def request_data(self, loc):
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = grpc_server.GcdmStub(channel)
            request_msg = grpc_msg.HeaderRequest(location=loc)
            data_msg = grpc_msg.DataRequest(location=loc, variable_spec=self.variable_spec)
            header_response = stub.GetNetcdfHeader(request_msg)

            # unpack the streaming response - we know that there is only one object being transmitted
            data_response = list(stub.GetNetcdfData(data_msg))[0]
            return self.decode_response(header_response, data_response)

    def decode_response(self, header, data):
        decoder = netCDF_Decode()
        return decoder.generate_file_from_response(header, data)

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


