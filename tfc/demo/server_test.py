import numpy as np
import netCDF4 as nc4
import sys
import requests
import aiohttp
import asyncio

async def make_request(url, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            response_json = await response.json()
            return np.array(response_json['predictions'])

def get_payload(nc, variable_spec):
    data = nc.variables[variable_spec][:].data
    data = data.reshape((1, *data.shape))
    return f'{{"instances" : {data.tolist()}}}'


# use this file to test interaction with tf server
if __name__ == '__main__':

    # get data from file
    fp = "/Users/rmcmahon/dev/awips-ml/tfc/demo/OR_ABI-L2-CMIPPR-M6C09_G16_s20212861650200_e20212861650200_c20212861650200.nc4"
    nc = nc4.Dataset(fp)

    # setup POST stuff
    payload = get_payload(nc, "Sectorized_CMI")
    url = 'http://localhost:8501/v1/models/model:predict'

    # POST to server via http
    model_response = asyncio.run(make_request(url, payload))
    print(model_response)

