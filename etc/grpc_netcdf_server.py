import grpc
from pygcdm.netcdf_encode import netCDF_Encode
from pygcdm.protogen import gcdm_server_pb2_grpc as grpc_server
from concurrent import futures


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


def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grpc_server.add_GcdmServicer_to_server(Responder(), server)
    server.add_insecure_port('[::]:6002')
    print('starting server...')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    server()
