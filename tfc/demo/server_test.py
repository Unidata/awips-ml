import numpy as np
import netCDF4 as nc4
import sys
import requests

# use this file to test interaction with tf server
if __name__ == '__main__':
    fp = "/Users/rmcmahon/dev/awips-ml/tfc/demo/OR_ABI-L2-CMIPPR-M6C09_G16_s20212861650200_e20212861650200_c20212861650200.nc4"
    nc = nc4.Dataset(fp)
    array = nc.variables['Sectorized_CMI'][:].data.reshape(1,890, 976)

    # POST to server via http
    url = 'http://localhost:8501/v1/models/model:predict'
    payload = f'{{"instances" : {array.tolist()}}}'
    response = requests.post(url, data=payload).json()
    response_array = np.array(response['predictions'])
    print("tf server response = \n")
    print(response_array)

