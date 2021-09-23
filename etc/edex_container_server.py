import grpc
from pygcdm.netcdf_encode import netCDF_Encode
from pygcdm.netcdf_decode import netCDF_Decode
from pygcdm.protogen import gcdm_server_pb2_grpc as grpc_server
from pygcdm.protogen import gcdm_netcdf_pb2 as grpc_msg
from concurrent import futures
import socket
import asyncio
import pathlib
import sys
import yaml

class AWIPSHandler():
    def __init__(self, trigger_port=6000, server_port=6001, client_port=6002, host="localhost"):
        # setup trigger event handler
        self.host = host
        self.trigger_port = trigger_port
        self.server_port = server_port
        self.client_port = client_port

        # setup pygcdm stuff
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_server.add_GcdmServicer_to_server(Responder(), self.server)
        self.server.add_insecure_port(f'{self.host}:{self.server_port}')
        self.request_handler = Requester(self.host, self.client_port)

        # start server/trigger
        asyncio.run(self.pygcdm_server_start())

    async def pygcdm_server_start(self):
        print('starting server...')
        self.server.start()
        while True:
            trigger = asyncio.create_task(self.trigger_listen())
            await trigger
            command = trigger.result()
            if command == "stop":
                print('stopping server based on remote command')
                self.server.stop(0)
                break
            elif command == "bad_path":
                print('bad path received; ignoring')
                pass
            else:
                if pathlib.Path(command).is_file():
                    print("requested file: ", command)
                    requested_data = self.request_handler.request_data()
                    print(requested_data)


    async def trigger_listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.trigger_port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024).decode('utf-8')
                if data == "stop":
                    conn.sendall(bytes('stop command recieved', 'utf-8'))
                    return data
                elif pathlib.Path(data).is_file():
                    conn.sendall(bytes('requesting data at specified path', 'utf-8'))
                    return data
                else:
                    conn.sendall(bytes('specified path does not exist', 'utf-8'))
                    return "bad_path"



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
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.loc = 'data/test.nc'
        self.variable_spec = 'analysed_sst'

    def request_data(self):
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = grpc_server.GcdmStub(channel)
            request_msg = grpc_msg.HeaderRequest(location=self.loc)
            data_msg = grpc_msg.DataRequest(location=self.loc, variable_spec=self.variable_spec)
            header_response = stub.GetNetcdfHeader(request_msg)

            # unpack the streaming response - we know that there is only one object being transmitted
            data_response = list(stub.GetNetcdfData(data_msg))[0]
            return self.decode_response(header_response, data_response)

    def decode_response(self, header, data):
        decoder = netCDF_Decode()
        return decoder.generate_file_from_response(header, data)


if __name__ == '__main__':
    print("starting AWIPSHandler")
    handler_type = sys.argv[1]
    with open("config.yaml") as file:
        config_dict = yaml.load(file, Loader=yaml.FullLoader)
    try: 
        assert handler_type in ["tf_container", "edex_container"]
    except AssertionError:
        raise SyntaxError("incorrect input argument; options are \"tf_container\" or \"edex_container\"")

    AWIPSHandler(**config_dict[handler_type])


""" to send messages use the following function (Imake sure ports match)
```
def send(msg, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', port))
        s.sendall(bytes(msg, 'utf-8'))
        data = s.recv(1024)
        print(data)
```
"""
