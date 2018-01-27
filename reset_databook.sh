#!/bin/bash

docker-compose -f docker-databook.yml down
sudo rm -rf data/*
rm -rf esdata/*

