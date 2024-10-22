FROM solr:6.6.6
RUN mkdir /opt/solr/server/solr/haystack
RUN cp -r server/solr/configsets/basic_configs/conf /opt/solr/server/solr/haystack
COPY ./tinxapi/managed-schema /opt/solr/server/solr/haystack/conf/managed-schema
