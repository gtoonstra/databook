#!/bin/bash

docker-compose -f docker-databook.yml down
sudo rm -rf docker/neo4j/data/*
rm -rf docker/elasticsearch/data/*
