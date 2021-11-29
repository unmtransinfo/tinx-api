#!/bin/bash

MYSQL_USER='root'

REQUIRED_TABLES="
tinx_articlerank
tinx_disease
tinx_importance
tinx_novelty
tinx_target
pubmed
protein
target
t2tc
do
do_parent
dto
"

for $tbl in $REQUIRED_TABLES
do
  mysqldump \
    -u ${MYSQL_USER} \
    --no-create-db \
    --compact \
    --skip-lock-tables \
    -e \
    --add-locks \
    --no-autocommit \
    -p tcrd $tbl > $tbl.sql
done


gzip tcrd_subset.sql


echo $REQUIRED_TABLES
