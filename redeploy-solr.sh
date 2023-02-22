#!/bin/bash
set -x
set -e

echo "trying to deploy the solr container"
echo "You may need to delete some crufty old container"
docker run -d -p 8983:8983 --name tinx-solr solr:6.6.6
docker exec -it tinx-solr mkdir /opt/solr/server/solr/haystack
docker exec -it tinx-solr cp -r server/solr/configsets/basic_configs/conf /opt/solr/server/solr/haystack
docker cp tinxapi/managed-schema tinx-solr:/opt/solr/server/solr/haystack/conf/managed-schema
echo "deployed solr container successfully"
echo "visit the SOLR admin panel (http://35.86.241.213:8983/) and create a core named haystack"



