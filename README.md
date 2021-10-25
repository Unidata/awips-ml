# awips-ml
awips-ml allows users to visualize [TensorFlow](https://www.tensorflow.org/) machine learning models witihin [AWIPS](https://www.unidata.ucar.edu/software/awips2/) via [CAVE](https://unidata.github.io/awips2/install/install-cave/).

![Example data being displayed](aux/example.png)

- [Quickstart](#tc_quickstart)
- [Interacting with the Containers](#tc_interact)
- [Modifying the Containers](#tc_modify)
- [Configuration](#tc_config)
- [Troubleshooting](#tc_troubleshooting)

## Quickstart<a name="tc_quickstart"></a>
These instructions assume that [Docker](https://docs.docker.com/get-docker/), [Docker Compose](https://docs.docker.com/compose/install/), and [CAVE](https://unidata.github.io/awips2/install/install-cave/) are installed (CAVE is required for viewing only). This git repository comes pre-loaded with example models so no configuration is required for demonstration purposes.

First, start by cloning this repository, building the containers (this will take ~20 minutes depending on internet speed), and launching then containers.
```
git clone https://github.com/rmcsqrd/awips-ml.git
cd awips-ml
docker-compose build
docker-compose up
```
Next, connect CAVE to the EDEX docker container. The default `docker-compose.yml` file is set such that the default CAVE port will be forwarded from the docker network namespace to the host OS network namespace. Connect by starting CAVE and entering your "EDEX Server" as `127.0.0.1` (or `localhost`) as shown:

![Connect CAVE to EDEX](aux/edex_server_localhost.png)

If a validation error occurs that is okay, sometimes it takes a while for the EDEX container to start; continue clicking "Validate" or "Start" until it says "Connected".

Once CAVE is opened, open the "Product Browser" via `CAVE > Data Browsers > Product Browser`. A window to the right side of the screen should appear. Load the original data and the data that has been run through the ML model via the Product Browser by clicking `Satellite > GOES-17 > WMESO-1 > CH...`.
- If `Satellite` is unavailable in the Product Browser, wait a few minutes and click the refresh button in the upper right-hand corner of the Product Browser.
- If no data appears in the product browser after waiting (~5min), the upstream LDM may be rejecting the EDEX containers requests; this is usually due to an invalid IP address (requests need to come from `.edu` IP address ranges or other approved IP address ranges) - see [Troubleshooting](#tc_troubleshooting).

When the data is loaded, your screen should look something like the image below. You can toggle the loaded data by clicking the text in the lower right-hand side of the "Map" window.

![Display Data via CAVE](aux/loaded_data.png)

You can shut down the EDEX containers by running
```
docker-compose down
```

## Interacting with the containers<a name="tc_interact"></a>
Sometimes it is useful to step into the containers to check on logs, files, etc. To do this, run the following [`exec`](https://docs.docker.com/engine/reference/commandline/exec/) command (this command assumes `bash` is installed in the container being accessed):
```
docker exec -it [container_name] bash
```
To view running containers, run `docker ps` which (if containers are running) should return something like this:
```
CONTAINER ID   IMAGE              COMMAND                  CREATED          STATUS          PORTS                                                                                                  NAMES
59abc5e97a8a   awips-ml_edex      "/usr/sbin/init"         31 minutes ago   Up 31 minutes   0.0.0.0:388->388/tcp, :::388->388/tcp, 0.0.0.0:9581-9582->9581-9582/tcp, :::9581-9582->9581-9582/tcp   edexc
e060cf1bb651   awips-ml_tf        "/usr/bin/tf_serving…"   31 minutes ago   Up 31 minutes   0.0.0.0:8500-8501->8500-8501/tcp, :::8500-8501->8500-8501/tcp                                          tfc
f3bfa05deec5   awips-ml_process   "python server/edex_…"   31 minutes ago   Up 31 minutes                                                                                                          processc
```
You can find `[container_name]` in the `NAMES` column of the output.

## Modifying the containers<a name="tc_modify"></a>
In general, anytime you modify any files, the containers need to be [rebuilt](https://docs.docker.com/compose/reference/build/). To do this, run the following commands:
```
docker-compose down
docker-compose build
docker-compose up
```


## Configuration<a name="tc_config"></a>
awips-ml is composed of three containers and some other directories which are all configurable according to user needs.
- `edexc`: this is the container that runs the actual EDEX server.
- `processc`: this is the container that takes data ingested by `edexc` and preprocesses before sending to `tfc` and post-processes data recieved from `tfc` before sending back to `edexc`.
- `tfc`: this is the container where the TensorFlow machine learning model exists.
- `server`: this directory has several common utilities used by different containers. Unless noted below, files in this directory should not be modified by users.
- `docker-compose.yml`: This file controls how `edexc`, `processc`, and `tfc` are launched/interact with each other. In general user configuration should not be necessary.
In general/where possible user configurations exist in specific files. Users should (in general) not need to modify any `Dockerfile` files.

#### edexc
This container has several configuration files that control the type of data ingested by EDEX and CAVE specific configuration. These files are all found in `edexc/etc/conf` - files in `edexc/etc/systemd` should not be modified by users. Unless noted below, files in `edexc/etc/conf` should not be edited by users:

###### `ldmd.conf`
This file controls the type of data ingested by the EDEX container. Note that several example entries are commented out. Users should modify this file so that the EDEX container ingests relevant data.

Modifications can be made by uncommenting an existing line or adding their own. The string in quotes is a regex statement that matches patterns on the upstream LDM. For example:
```
REQUEST UNIWISC|NIMAGE "OR_ABI-L2-CMIPM1-M6C09_G17.*" iddc.unidata.ucar.edu      # GOES Channel 9 Mesoscale 1
```
Is requesting `OR_ABI-L2-CMIPM1-M6C09_G17.*` all GOES 17 (G17) Advanced Baseline Imager (ABI) Level 2 (L2) products with product name Cloud & Moisture Imagery (CMIP) in the Mesoscale 1 (M1) ABI scene. Channel 09 (M6C09) is the specific channel being requested which corresponds to Mid-level water vapor. Info on file naming conventions for `ldmd.conf` can be found at the following links:
- [http://edc.occ-data.org/goes16/getdata/#file-formats](http://edc.occ-data.org/goes16/getdata/#file-formats)
- [http://cimss.ssec.wisc.edu/goes/ABI_File_Naming_Conventions.pdf](http://cimss.ssec.wisc.edu/goes/ABI_File_Naming_Conventions.pdf)

The upstream LDM which the EDEX container gets data from is specified by `iddc.unidata.ucar.edu`. Users must select an upstream LDM that is willing to serve them data.

###### `pqact.conf`
The `pqact.conf` file handles actions as the EDEX container ingests new data from the upstream LDM. Documentation on this file can be found [here](https://www.unidata.ucar.edu/software/ldm/ldm-current/basics/pqact.conf.html). A relevant example for GOES cloud and moisture data is:
```
NIMAGE  ^/data/ldm/pub/native/satellite/GOES/([^/]*)/Products/CloudAndMoistureImagery/([^/]*)/([^/]*)/([0-9]{8})/([^/]*)(c[0-9]{7})(..)(.....)_ml.nc
    FILE    -close -edex    /awips2/data_store/GOES/\4/\7/CMI-IDD/\5\6\7\8_ml.nc4  # handle inputs for awips-ml

NIMAGE  ^/data/ldm/pub/native/satellite/GOES/([^/]*)/Products/CloudAndMoistureImagery/([^/]*)/([^/]*)/([0-9]{8})/([^/]*)(c[0-9]{7})(..)(.....).nc
    EXEC    /home/awips/anaconda3/envs/grpc_env/bin/python /server/trigger.py /awips2/data_store/GOES/\4/\7/CMI-IDD/\5\6\7\8.nc4 edex_container
```
Note that the two entries have similar pattern matching with different commands as described in the `pqact.conf` documentation linked above. The major difference here is the inclusion of the `EXEC` entry which calls a python script that alerts the EDEX container of a newly recieved file and sends it to the `tfc` container.

###### `registry.xml`
Use this filename to change the hostname:
```
<hostname>[name].docker</hostname>
```

#### tfc
The `tfc` container is designed to be lightweight in the sense that users only need to point to the location of their trained model. Users can do this by modifying `tfc/Dockerfile`:
```
COPY ./tfc/models/[saved_model] /models/model
```
Where `[saved_model]` is the location of the model they'd like to serve with the `tfc` container. Note that `[saved_model]` must conform to this directory structure:
```
[saved_model]/[version_number]/
```
because the underlying TensorFlow docker image in `tfc` needs a version number to run.

#### processc
This container does not have any configuration options associated with it.

#### server
This folder contains several configuration files/scripts used for handling data I/O from the `edexc`/EDEX server. Users do not need to modify the `edex_container_server.py` or `trigger.py` files directly as these can be controlled with `config.yaml`

###### `config.yaml`
The main parameter to change in this file is `variable_spec` - this is the `netCDF` variable that is passed between `edexc` and `processc` (and eventually `tfc`).

Besides this, `config.yaml` controls several aspects of the inter-container networking and which ports the `edexc` and `processc` containers communicate with each other; in general these ports do not need to be modified as they are restricted to the docker network namespace so they shouldn't interfere with the host OS's network namespace.


## Troubleshooting<a name="tc_troubleshooting"></a>
This section covers common problems. If your question is not answered here, feel free to open a [new issue](https://github.com/rmcsqrd/awips-ml/issues) for help.

#### What should I do if:
###### No data is available in the CAVE Product Browser:
- Try waiting for a few minutes to see if data loads - sometimes there is a lag between launching the EDEX container and when data is available.
- If no data eventually appears, interact with the container and check the LDM log by:
```
docker exec -it edexc bash
less /awips2/ldm/logs/ldmd.log
```
Within this log file, you should see something similar to:
```
20211021T183357.073945Z iddc.unidata.ucar.edu[1111] requester6.c:make_request:311       NOTE  Upstream LDM-6 on iddc.unidata.ucar.edu is willing to be a primary feeder
```
If you do not see a message like this, that means that whatever upstream LDM specified in the `ldmd.conf` file is rejecting your requests. Generally this means your IP address is being rejected. Contact the upstream LDM administrator for more information. In the case of Unidata LDM's, your IP address needs to be associated with a `.edu` domain.

###### My containers keep crashing
Generally it is convenient to launch a container in detached mode (`docker-compose up -d`), however this means that you can't see the output of the container. If your container is crashing it can be convenient to launch the container normally (`docker-compose up`) and view the output (especially for the `processc`/`tfc` containers).

Additionally it can be useful to look at the outputs of the containers themselves by attaching to the container process launched by `docker-compose`; you can do this via:
```
docker attach [container_name]
```

###### Stuff just doesn't work
File an issue (ideally with a link to your forked `awips-ml` repository). Useful places to look for logs within the `edexc` container are:
- `awips2/edex/logs/edex-ingest-[product_type]-[date].log`
- `awips2/ldm/logs/ldmd.log`
- The output of the python script handling communication between `edexc` and `tfc` can be viewed via the following command within the `edexc` container:
```
sudo journalctl -fu listener_start.service
```
