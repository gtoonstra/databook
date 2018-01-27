#!/bin/bash

source venv/bin/activate

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $DIR
export PYTHONPATH=$PYTHONPATH:${DIR}

databook/bin/databook webserver
