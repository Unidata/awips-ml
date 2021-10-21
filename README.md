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
Next, connect CAVE to the EDEX docker container. The default `docker-compose.yml` file is set such that the default CAVE port will be forwarded from the docker network namespace to the host OS network namespace.

Start both containers:
```
docker-compose up -d
```
Sometimes if there is an error it helps to see what compose is doing by omitting the `-d` flag.

Access running container:
```
docker exec -it [container name] bash
```

Shutdown docker-compose launched containers
```
docker-compose down
```

Rebuild after modification to `Dockerfile`
```
docker-compose build
```

## BONE do test
```
docker-compose up -d
[open bash in tfc container, attach to process in edexc container]
[do this in tfc container]
python
import test
test.send("cat", "edexc", 6000)  # this works
test.send("test.nc", "edexc", 6000)  # this should work but crashes program. I think this is because grpc is trying to send over localhost but this needs to be changed to "tfc" (or "edexc" if being executed from other container, do this in yaml)
```

## Info on file naming conventions for `ldmd.conf`
[http://edc.occ-data.org/goes16/getdata/#file-formats](http://edc.occ-data.org/goes16/getdata/#file-formats)
[http://cimss.ssec.wisc.edu/goes/ABI_File_Naming_Conventions.pdf](http://cimss.ssec.wisc.edu/goes/ABI_File_Naming_Conventions.pdf)
