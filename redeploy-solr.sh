#!/bin/bash
set -x
set -e

echo "trying to deploy the solr container"
docker stop tinx-solr
docker rm tinx-solr
docker run -d -p 8983:8983 --name tinx-solr solr:6.6.6
docker exec -it tinx-solr mkdir /opt/solr/server/solr/haystack
docker exec -it tinx-solr cp -r server/solr/configsets/basic_configs/conf /opt/solr/server/solr/haystack
docker cp tinxapi/managed-schema tinx-solr:/opt/solr/server/solr/haystack/conf/managed-schema
docker exec -it tinx-solr solr create_core -c haystack -p 8983
echo "deployed solr container successfully"
echo "You may visit the SOLR admin panel here: http://35.86.241.213:8983/"
echo "updating indices"
./update_solr_index.sh
