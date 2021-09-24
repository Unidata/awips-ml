# awips-ml
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
