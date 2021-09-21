import grpc
from pygcdm.protogen import gcdm_netcdf_pb2 as grpc_msg
from pygcdm.protogen import gcdm_server_pb2_grpc as grpc_server
from pygcdm.netcdf_decode import netCDF_Decode


def run():
    with grpc.insecure_channel('localhost:1234') as channel:
        stub = grpc_server.GcdmStub(channel)
        loc = 'data/test.nc'
        variable_spec = 'analysed_sst'
        request_msg = grpc_msg.HeaderRequest(location=loc)
        data_msg = grpc_msg.DataRequest(location=loc, variable_spec=variable_spec)
        header_response = stub.GetNetcdfHeader(request_msg)

        # unpack the streaming response - we know that there is only one object being transmitted
        data_response = list(stub.GetNetcdfData(data_msg))[0]

        return decode_response(header_response, data_response)


def decode_response(header, data):
    decoder = netCDF_Decode()
    return decoder.generate_file_from_response(header, data)


if __name__ == '__main__':
    response = run()
    print(response)
