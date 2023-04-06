#!/bin/bash
docker container stop tinx-app
docker container rm tinx-app
docker run -d --name=tinx-app -v "$PWD:/tinx" -p 8000:8000 --network="host" -ti tinx


