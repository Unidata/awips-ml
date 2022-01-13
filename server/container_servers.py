import grpc
from pygcdm.protogen import gcdm_server_pb2_grpc as grpc_server
from grpc_api import Responder, Requester
import socket
import queue
import pathlib
from concurrent import futures
import asyncio
import aiohttp
import sys
import yaml
import numpy as np
import xarray as xr
import netCDF4 as nc4
import subprocess
from preproc import preproc  # custom user pre/post-processing scripts
from postproc import postproc

EDEX_PYTHON_LOCATION = "/awips2/python/bin/python"
EDEX_QPID_NOTIFICATION = "/awips2/ldm/dev/notifyAWIPS2-unidata.py"

class BaseServer():
    """
    Base class for pygcdm file transfer between edexc and processc containers.

    Description
    ---------
    This class is responsible for container agnostic network functionality. At a high
    level the BaseServer has two components:
    1) Trigger: Receives strings describing the filepath of the netCDF file to request
            in other container. Places the received filepath into a queue which
            triggers the responder/requester.
    2) Responder/Requester: Activates when a filepath is placed into the queue and 
            requests the file via pygcdm. pygcdm only sends data when requested which
            is why it is implemented this way. The Requester makes the request and the
            Responder responds to the request.

    Attributes
    ---------
    fp_queue: 
        queue item containing remote filepaths to request via pygcdm
    variable_spec: 
        netCDF variable to request via pygcdm
    **kwargs: 
        network variables (hostnames, ports, docker network) defined in /usr/config.yaml
    """

    def __init__(self, fp_queue, variable_spec, **kwargs):

        # unpack args
        self.variable_spec = variable_spec
        self.fp_queue = fp_queue

        # unpack kwargs
        for name, value in kwargs.items():
            setattr(self, name, value)

        # start gRPC servers
        self.init_responder_server()
        self.init_requester_server()

    def init_responder_server(self):
        """
        Initialize gRPC Responder (intakes Requests and returns Responses).
        """

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_server.add_GcdmServicer_to_server(Responder(), self.server)
        self.server.add_insecure_port(f'{self.pygcdm_client}:{self.tx_port}')
        print(f"responding to grpc requests on {self.pygcdm_client}:{self.tx_port}")
        self.server.start()

    def init_requester_server(self):
        """
        Initialize gRPC Requester (sends Requests and receives Responses).
        """

        self.request_handler = Requester(self.pygcdm_server, self.rx_port, self.variable_spec)
        print(f"making grpc requests on {self.pygcdm_server}:{self.rx_port}")

    async def trigger_listener(self):
        """
        Listen for trigger messages (strings with remote file location).
        """

        trigger_server = await asyncio.start_server(
                self.handle_trigger, self.host, self.rx_port_trigger)
        print(f"listening for file paths to request on {self.host}:{self.rx_port_trigger}...")
        async with trigger_server:
            await trigger_server.serve_forever()

    async def handle_trigger(self, reader, writer):
        """
        Append trigger messages to queue.
        """

        data = await reader.read()
        message = data.decode()
        await self.fp_queue.put(message)

class ProcessContainerServer(BaseServer):
    """
    processc container server in charge of requesting data from edexc, sending to tfc,
        and sending trigger message back to edexc.
    """
    def __init__(self, fp_queue, variable_spec, **kwargs):
        super().__init__(fp_queue, variable_spec, **kwargs)
        self.variable_spec = variable_spec

    async def pygcdm_requester(self):
        """
        Function that indefinitely reads filepaths from trigger queue, requests netCDF
            file from edexc, sends file to tfc, and sends trigger message to edexc 
            with tfc output.
        """

        while True:
            file_loc = await self.fp_queue.get()
            print(f"trigger file to request: {file_loc}")
            print(f"current queue size = {self.fp_queue.qsize()}")
            nc_file = await self.request_handler.request_data(file_loc)

            # first send netcdf file data to tf container
            url = f'{self.ml_model_location}:predict'
            request = self.netcdf_to_request(nc_file, self.variable_spec)
            response = await self.make_request(url, request)

            if response == 'error':  
                # error handling is printed to log in make_request
                pass
            else:
                
                # then update netcdf (in place) with values from tensorflow, and save to a path,
                # reuse path structure from edex container
                self.response_to_netcdf(nc_file, response, self.variable_spec)
                fp = pathlib.Path(file_loc)
                fp.mkdir(parents=True, exist_ok=True)
                fp_ml = fp.with_stem(fp.stem + '_ml')
                nc_file.to_netcdf(fp_ml)  # this saves to path

                # finally send file location back to edex so it can request via pygcdm
                reader, writer = await asyncio.open_connection(
                        self.pygcdm_server, self.tx_port_trigger)
                writer.write(str(fp_ml).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()

    async def make_request(self, url, data):
        """
        Function that sends pre-processed data to tfc container and returns response (ML model output).
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                response_json = await response.json()
                try:
                    return np.array(response_json['predictions'])
                except KeyError:
                    # if missing 'predictions' key then model could not process sent data
                    print(f"Error with tensorflow model:\n{response_json}")
                    return 'error'
                except:
                    return 'error'
    
    def netcdf_to_request(self, nc, variable_spec):
        """
        Function that converts netCDF file using user define pre-processing script and 
            returns numpy array to send to tfc container.
        """

        data = nc.variables[variable_spec][:].data
        data = data.reshape((1, *data.shape))
        data = preproc(data)
        return f'{{"instances" : {data.tolist()}}}'

    def response_to_netcdf(self, nc, response, variable_spec):
        """
        Function that converts tfc container ML output using user defined post-processing 
            script and re-packs into netCDF file. 
        """

        response = postproc(response)
        nc.variables[variable_spec][:] = response.squeeze()  # okay if this is redundant

class EDEXContainerServer(BaseServer):
    """
    edexc container server in charge of requesting data from processc.
    """
    def __init__(self, fp_queue, variable_spec, **kwargs):
        super().__init__(fp_queue, variable_spec, **kwargs)
        self.variable_spec = variable_spec

    async def pygcdm_requester(self):
        """
        Function that indefinitely reads filepaths from trigger queue and requests 
            data from processc
        """
        while True:
            file_loc = await self.fp_queue.get()
            print(f"trigger file to request: {file_loc}")
            print(f"current queue size = {self.fp_queue.qsize()}")
            nc_file = await self.request_handler.request_data(file_loc)

            # start by copying old file to new on edex container
            fp_ml = pathlib.Path(file_loc)  # the received path will have _ml appended
            fp = fp_ml.with_stem(fp_ml.stem.replace('_ml', ''))
            og_nc_file = xr.open_dataset(fp, mask_and_scale=False)
            og_nc_file[self.variable_spec].data = nc_file[self.variable_spec].data
            nc_file = og_nc_file.rename_vars({self.variable_spec:self.variable_spec+'_ml'})
            nc_file.to_netcdf(fp_ml)

            # we call via subprocess because qpid notifier is written for python 2 not 3
            # view output via sudo journalctl -fu listener_start.service
            # the way this works should be by checking returncode (nonzero = fails) then printing stderr otherwise say nothing
            proc_qpid = subprocess.run([EDEX_PYTHON_LOCATION,
                EDEX_QPID_NOTIFICATION,
                str(fp_ml)],
                capture_output=True,
                )
            if proc_qpid.returncode == 1:
                print(f"Error ingesting file into EDEX. Error response:\n\
                        {proc_qpid.stderr}")
            else:
                print(f"File successfully ingested into EDEX")
            sys.stdout.flush()
            sys.stderr.flush()

async def run_server(configs, variable_spec, process_type):
    # start up appropriate server type
    if process_type == 'process_container':
        server = ProcessContainerServer(asyncio.Queue(), variable_spec, **configs)
    elif process_type == 'edex_container':
        server = EDEXContainerServer(asyncio.Queue(), variable_spec, **configs)
    else:
        try:
            assert process_type in ["process_container", "edex_container"]
        except AssertionError:
            raise SyntaxError("incorrect input argument; options are \"process_container\" or \"edex_container\"")
    
    # run server indefinitely
    g = await asyncio.gather(server.trigger_listener(), server.pygcdm_requester())

if __name__=="__main__":
    process_type = sys.argv[1]
    with open("server/config.yaml") as file:
        config_dict = yaml.load(file, Loader=yaml.FullLoader)

    asyncio.run(run_server(config_dict[process_type], 
        config_dict['variable_spec'], 
        process_type))


