import grpc
from pygcdm.netcdf_encode import netCDF_Encode
from pygcdm.netcdf_decode import netCDF_Decode
from pygcdm.protogen import gcdm_server_pb2_grpc as grpc_server
from pygcdm.protogen import gcdm_netcdf_pb2 as grpc_msg

MAX_MESSAGE_LENGTH = 1000*1024*1024


class Responder(grpc_server.GcdmServicer):

    def __init__(self):
        self.encoder = netCDF_Encode()

    def GetNetcdfHeader(self, request, context):
        return self.encoder.generate_header_from_request(request)

    def GetNetcdfData(self, request, context):
        # stream the data response
        data_response = [self.encoder.generate_data_from_request(request)]
        for data in data_response:
            yield(data)


class Requester():
    def __init__(self, host, port, var_spec):
        self.host = host
        self.port = port
        self.variable_spec = var_spec

    async def request_data(self, loc):
        options = [('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
                   ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH)]
        async with grpc.aio.insecure_channel(f'{self.host}:{self.port}',
                options=options) as channel:
            stub = grpc_server.GcdmStub(channel)
            print(f"requesting data from {self.host}:{self.port}")
            request_msg = grpc_msg.HeaderRequest(location=loc)
            data_msg = grpc_msg.DataRequest(location=loc,
                    variable_spec=self.variable_spec)

            # async unpack the streaming response; data_response is one item
            header_response = await stub.GetNetcdfHeader(request_msg)
            data_response = [data async for data in
                    stub.GetNetcdfData(data_msg)][0]

            return self.decode_response(header_response, data_response)

    def decode_response(self, header, data):
        decoder = netCDF_Decode()
        return decoder.generate_file_from_response(header, data)
