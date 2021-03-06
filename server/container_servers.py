import grpc
from pygcdm.protogen import gcdm_server_pb2_grpc as grpc_server
from grpc_api import Responder, Requester
import pathlib
from concurrent import futures
import asyncio
import aiohttp
import sys
import os
import yaml
import numpy as np
import xarray as xr
import subprocess
from preproc import preproc  # custom user pre/post-processing scripts
from postproc import postproc
from datetime import date

EDEX_PYTHON_LOCATION = "/awips2/python/bin/python"
EDEX_QPID_NOTIFICATION = "/awips2/ldm/dev/notifyAWIPS2-unidata.py"


class BaseServer():
    """
    Base class for pygcdm file transfer between edexc and processc containers.

    Description
    ---------
    This class is responsible for container agnostic network functionality.
    At a high level the BaseServer has two components:
    1) Trigger: Receives strings describing the filepath of the netCDF file to
            request in other container. Places the received filepath into a
            queue which triggers the responder/requester.
    2) Responder/Requester: Activates when a filepath is placed into the queue
            and requests the file via pygcdm. pygcdm only sends data when
            requested which is why it is implemented this way. The Requester
            makes the request and the Responder responds to the request.

    Attributes
    ---------
    pygcdm_queue:
        queue item containing remote filepaths to request via pygcdm
    variable_spec:
        netCDF variable to request via pygcdm
    **kwargs:
        network variables (hostnames, ports, docker network) defined in
        /usr/config.yaml
    """

    def __init__(self, pygcdm_queue, variable_spec, **kwargs):

        # unpack args
        self.variable_spec = variable_spec
        self.pygcdm_queue = pygcdm_queue

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
        print(f"responding to grpc requests on {self.pygcdm_client}:\
                {self.tx_port}")
        self.server.start()

    def init_requester_server(self):
        """
        Initialize gRPC Requester (sends Requests and receives Responses).
        """

        self.request_handler = Requester(self.pygcdm_server,
                self.rx_port,
                self.variable_spec)
        print(f"making grpc requests on {self.pygcdm_server}:{self.rx_port}")

    async def trigger_listener(self):
        """
        Listen for trigger messages (strings with remote file location).
        """

        trigger_server = await asyncio.start_server(
                self.handle_trigger, self.host, self.rx_port_trigger)
        print(f"listening for file paths to request on {self.host}:\
                {self.rx_port_trigger}...")
        async with trigger_server:
            await trigger_server.serve_forever()

    async def handle_trigger(self, reader, writer):
        """
        Append trigger messages to queue.
        """

        data = await reader.read()
        message = data.decode()
        await self.pygcdm_queue.put(message)


class ProcessContainerServer(BaseServer):
    """
    processc container server in charge of requesting data from edexc,
    sending to tfc, and sending trigger message back to edexc.
    """
    def __init__(self, pygcdm_queue, variable_spec, **kwargs):
        super().__init__(pygcdm_queue, variable_spec, **kwargs)
        self.variable_spec = variable_spec

    async def pygcdm_requester(self):
        """
        Function that indefinitely reads filepaths from trigger queue, requests
            netCDF file from edexc, sends file to tfc, and sends trigger
            message to edexc with tfc output.
        """

        while True:
            # get from queue
            file_loc = await self.pygcdm_queue.get()
            print(f"trigger file to request: {file_loc}")
            print(f"current processc queue size = {self.pygcdm_queue.qsize()}")
            nc_file = await self.request_handler.request_data(file_loc)

            # first send netcdf file data to tf container
            url = f'{self.ml_model_location}:predict'
            request = self.netcdf_to_request(nc_file, self.variable_spec)
            response = await self.make_request(url, request)

            if response == 'error':
                # error handling is printed to log in make_request
                pass
            else:
                # then update netcdf (in place) with values from tensorflow,
                #   and save to a path,
                # reuse path structure from edex container
                self.response_to_netcdf(nc_file, response, self.variable_spec)
                fp = pathlib.Path(file_loc)
                fp.mkdir(parents=True, exist_ok=True)
                fp_ml = fp.with_stem(fp.stem + '_ml')
                nc_file.to_netcdf(fp_ml)  # this saves to path

                # then, send file location back to edex for request via pygcdm
                reader, writer = await asyncio.open_connection(
                        self.pygcdm_server, self.tx_port_trigger)
                writer.write(str(fp_ml).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()

    async def make_request(self, url, data):
        """
        Function that sends pre-processed data to tfc container and returns
        response (ML model output).
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                response_json = await response.json()
                try:
                    return np.array(response_json['predictions'])
                except KeyError:
                    # if missing 'predictions' key then model could not process
                    #   sent data
                    print(f"Error with tensorflow model:\n{response_json}")
                    return 'error'
                except Exception:
                    return 'error'

    def netcdf_to_request(self, nc, variable_spec):
        """
        Function that converts netCDF file using user define pre-processing
        script and returns numpy array to send to tfc container.
        """

        data = nc.variables[variable_spec][:].data
        data = data.reshape((1, *data.shape))
        data = preproc(data)
        return f'{{"instances" : {data.tolist()}}}'

    def response_to_netcdf(self, nc, response, variable_spec):
        """
        Function that converts tfc container ML output using user defined
        post-processing script and re-packs into netCDF file.
        """

        response = postproc(response)
        # okay if this is redundant
        nc.variables[variable_spec][:] = response.squeeze()


class EDEXContainerServer(BaseServer):
    """
    edexc container server in charge of requesting data from processc.
    """
    def __init__(self, pygcdm_queue, variable_spec, **kwargs):
        super().__init__(pygcdm_queue, variable_spec, **kwargs)
        self.variable_spec = variable_spec
        self.edex_started = False
        self.edex_ingest_queue = asyncio.Queue()

    async def pygcdm_requester(self):
        """
        Function that indefinitely reads filepaths from trigger queue and
        requests data from processc
        """
        while True:
            # get from queue 
            file_loc = await self.pygcdm_queue.get()
            print(f"trigger file to request: {file_loc}")
            print(f"current edexc queue size = {self.pygcdm_queue.qsize()}")
            nc_file = await self.request_handler.request_data(file_loc)

            # start by copying old file to new on edex container
            # the received path will have _ml appended
            fp_ml = pathlib.Path(file_loc)
            fp = fp_ml.with_stem(fp_ml.stem.replace('_ml', ''))
            og_nc_file = xr.open_dataset(fp, mask_and_scale=False)
            og_nc_file[self.variable_spec].data = nc_file[self.variable_spec].data
            nc_file = og_nc_file.rename_vars(
                    {self.variable_spec: self.variable_spec+'_ml'}
                    )
            nc_file.to_netcdf(fp_ml)

            # check to see if EDEX is started
            if not self.edex_started:
                self.check_edex_started()

            # if EDEX has started ...
            if self.edex_started:

                # ...and there are items in the queue then drain it first (do this once)
                while not self.edex_ingest_queue.empty():
                    print(f"EDEX started, ingesting backlog of queued files")
                    print(f"Current ingestion backlog queue size = {self.edex_ingest_queue.qsize()}")
                    ingest_fp = await self.edex_ingest_queue.get()
                    print(f"Ingesting backlog file: {ingest_fp}")
                    self.edex_ingest(ingest_fp)

                # else just ingest the new file
                print(f"Ingesting new file into EDEX")
                self.edex_ingest(fp_ml)

            # else if EDEX not started then put into queue for ingestion
            else:
                print(f"EDEX not started, adding file to ingest queue")
                print(f"Current ingestion backlog queue size = {self.edex_ingest_queue.qsize()}")
                await self.edex_ingest_queue.put(fp_ml)

            # finally flush buffer for logging in docker
            self.flush_buffer()
    
    def edex_ingest(self, fp_ml):
        """
        A utility function that uses the subprocess module to call the EDEX ingestion script.

        We use subprocess because the notifyAWIPS2-unidata.py script only works with python 2
        but the rest of this code needs to be run with python 3.
        """

        # first make sure we're dealing with strings
        if not isinstance(fp_ml, str):
            fp_ml = str(fp_ml)
        
        # then, notify qpid of new file
        proc_qpid = subprocess.run([EDEX_PYTHON_LOCATION,
            EDEX_QPID_NOTIFICATION,
            fp_ml],
            capture_output=True,
            )

        # finally process the output
        if proc_qpid.returncode == 1:
          if "'external.dropbox' not found" in proc_qpid.stderr.decode('utf-8'):
            print(f"Error ingesting file into EDEX: EDEX not operational yet.")
          else:
            print(f"Error ingesting file into EDEX. Error response:\n\
              {proc_qpid.stderr}")
        else:
          print("File successfully ingested into EDEX")

    def check_edex_started(self):
        """
        Function that checks if EDEX is operational.

        EDEX takes some time to start up after initial "edex start"
        command and any calls to `IngestViaQPID()` will return an
        error. This function parses the EDEX logfiles for a string
        that indicates when EDEX has started fully.
        """

        # check if edex log file has been created
        d = date.today().strftime("%Y%m%d")
        print("CHECKING EDEX STATUS")
        if f'edex-ingest-{d}.log' in os.listdir('/awips2/edex/logs'):
            edex_check = subprocess.run(['grep', 
                'EDEX ESB is now operational', 
                f'awips2/edex/logs/edex-ingest-{d}.log'], 
                capture_output=True)


            # then check if edex is operational
            if edex_check.stdout.decode('utf-8') != '':
                print("EDEX Status: OPERATIONAL")
                self.edex_started = True
            else:
                print("EDEX Status: NOT OPERATIONAL")

    def flush_buffer(self):
        """
        Function that flushes print buffer to show up in edexc docker log
        """
        sys.stdout.flush()
        sys.stderr.flush()

async def run_server(configs, variable_spec, process_type):
    # start up appropriate server type
    if process_type == 'process_container':
        server = ProcessContainerServer(asyncio.Queue(),
                variable_spec,
                **configs
                )
    elif process_type == 'edex_container':
        server = EDEXContainerServer(asyncio.Queue(),
                variable_spec,
                **configs
                )
    else:
        try:
            assert process_type in ["process_container", "edex_container"]
        except AssertionError:
            raise SyntaxError("incorrect input argument; options are \
                    \"process_container\" or \"edex_container\"")

    # run server indefinitely
    await asyncio.gather(server.trigger_listener(), server.pygcdm_requester())

if __name__ == "__main__":
    process_type = sys.argv[1]
    with open("server/config.yaml") as file:
        config_dict = yaml.load(file, Loader=yaml.FullLoader)

    asyncio.run(run_server(config_dict[process_type],
        config_dict['variable_spec'],
        process_type))
