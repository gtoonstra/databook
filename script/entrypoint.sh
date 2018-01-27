#!/usr/bin/env bash

AIRFLOW_HOME="/usr/local/databook"
CMD="databook"
TRY_LOOP="20"

# Install custom python package if requirements.txt is present
if [ -e "/requirements.txt" ]; then
    $(which pip) install --user -r /requirements.txt
fi

exec $CMD databook
