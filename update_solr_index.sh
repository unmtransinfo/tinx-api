#!/bin/bash
echo "updating SOLR index, this script assumes you ran your container with name tinx-app"
docker exec -it tinx-app python manage.py update_index
docker exec -it tinx-app python tinxapi/metadata.py
