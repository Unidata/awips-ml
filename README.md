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
