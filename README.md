# awips-ml
`awips-ml` allows users to visualize [TensorFlow](https://www.tensorflow.org/) machine learning models witihin [AWIPS](https://www.unidata.ucar.edu/software/awips2/) via [CAVE](https://unidata.github.io/awips2/install/install-cave/).

## Quickstart
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

Once CAVE is opened, open the "Product Browser" via `CAVE > Data Browsers > Product Browser`. A window to the right side of the screen should appear. Load the original data and the data that has been run through the ML model via the Product Browser by clicking `Satellite > GOES-17 > WMESO-1 > CH...`. If `Satellite` is unavailable in the Product Browser, wait a few minutes and click the refresh button in the upper right-hand corner of the Product Browser.

When the data is loaded, your screen should look something like the image below. You can toggle the loaded data by clicking the text in the lower right-hand side of the "Map" window.

![Display Data via CAVE](aux/loaded_data.png)

You can shut down the EDEX containers by running
```
docker-compose down
```

## Interacting with the containers
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

## Modifying the containers
In general, anytime you modify any files, the containers need to be [rebuilt](https://docs.docker.com/compose/reference/build/). To do this, run the following commands:
```
docker-compose down
docker-compose build
docker-compose up
```

## Troubleshooting

## Configuration

#### `edexc`
Info on file naming conventions for `ldmd.conf` can be found at the following links:
- [http://edc.occ-data.org/goes16/getdata/#file-formats](http://edc.occ-data.org/goes16/getdata/#file-formats)
- [http://cimss.ssec.wisc.edu/goes/ABI_File_Naming_Conventions.pdf](http://cimss.ssec.wisc.edu/goes/ABI_File_Naming_Conventions.pdf)

#### `tfc`

#### `processc`
