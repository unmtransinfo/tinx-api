#!/bin/bash
docker run -v $PWD:/tinx -p 8000:8000 --network="host" -ti tinx
