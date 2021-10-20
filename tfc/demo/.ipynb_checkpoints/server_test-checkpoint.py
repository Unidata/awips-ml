import numpy as np
import netCDF4 as nc4
import sys
import aiohttp
import asyncio

async def make_request(url, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            response_json = await response.json()
            return np.array(response_json['predictions'])

def netcdf_to_request(nc, variable_spec):
    data = nc.variables[variable_spec][:].data
    data = data.reshape((1, *data.shape))
    return f'{{"instances" : {data.tolist()}}}'

def response_to_netcdf(nc, response, variable_spec):
    nc.variables[variable_spec][:] = response

# use this file to test interaction with tf server
if __name__ == '__main__':

    # get data from file
    fp = "/Users/rmcmahon/dev/awips-ml/tfc/demo/OR_ABI-L2-CMIPPR-M6C09_G16_s20212861650200_e20212861650200_c20212861650200.nc4"
    nc = nc4.Dataset(fp, mode='r+')

    # setup POST stuff
    var_spec = 'Sectorized_CMI'
    request = netcdf_to_request(nc, var_spec)
    url = 'http://localhost:8501/v1/models/model:predict'

    # POST to server via http
    response = asyncio.run(make_request(url, request))
    response_to_netcdf(nc, response, var_spec)

