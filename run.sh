#!/bin/bash
docker run -v -d --name=tinx-app $PWD:/tinx -p 8000:8000 --network="host" -ti tinx
