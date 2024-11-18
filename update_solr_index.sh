#!/bin/bash
echo "updating SOLR index, this script assumes you ran your container with name tinx-app"
docker exec -it tinx-api-tinx_api-1 python manage.py update_index
docker exec -it tinx-api-tinx_api-1 python tinxapi/metadata.py
