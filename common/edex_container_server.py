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
    def __init__(self, trigger_port=6000, server_port=6001, client_port=6002, host="localhost", pygcdm_client="localhost", pygcdm_server="localhost", variable_spec=""):
        # setup trigger event handler
        self.trigger_port = trigger_port
        self.server_port = server_port
        self.client_port = client_port
        self.host = host
        self.pygcdm_client = pygcdm_client
        self.pygcdm_server = pygcdm_server
        self.variable_spec = variable_spec

        # setup pygcdm stuff
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_server.add_GcdmServicer_to_server(Responder(), self.server)
        self.server.add_insecure_port(f'{self.pygcdm_client}:{self.server_port}')
        self.request_handler = Requester(self.pygcdm_server, self.client_port, self.variable_spec)

        # start server/trigger
        print('starting server...')
        self.server.start()
        while True:  # BONE this should handle stop command
            asyncio.run(self.pygcdm_server_run())

    async def pygcdm_server_run(self):
        trigger = asyncio.create_task(self.trigger_listen())
        await trigger
        command = trigger.result()
        if command == "stop":
            print('stopping server based on remote command')
            self.server.stop(0)
        elif command == "bad_path":
            print('bad path received; ignoring')
        else:
            print("requested file: ", command)
            try:
                requested_data = self.request_handler.request_data(command)
                print(requested_data)
            except grpc.RpcError as e:
                print("GRPC ERROR:")
                print("Error Details: ",e.details())
                status_code = e.code()
                print("Error Status Code Name: ", status_code.name)
                print("Error Status Code Value: ",status_code.value, "\n")
            else:
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
                else:
                    conn.sendall(bytes('requesting data at specified path', 'utf-8'))
                    return data


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
