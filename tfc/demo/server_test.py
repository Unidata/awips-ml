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

# use this file to test interaction with tf server
if __name__ == '__main__':
    fp = "/Users/rmcmahon/dev/awips-ml/tfc/demo/OR_ABI-L2-CMIPPR-M6C09_G16_s20212861650200_e20212861650200_c20212861650200.nc4"
    nc = nc4.Dataset(fp)
    array = nc.variables['Sectorized_CMI'][:].data.reshape(1,890, 976)

    # POST to server via http
    url = 'http://localhost:8501/v1/models/model:predict'
    payload = f'{{"instances" : {array.tolist()}}}'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(make_request(url, payload))

