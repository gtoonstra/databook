#!/usr/bin/env bash

AIRFLOW_HOME="/usr/local/airflow"
CMD="airflow"
TRY_LOOP="20"

: ${SQL_HOST:="airflow-db"}
: ${SQL_PORT:="3306"}
: ${SQL_DATABASE:="airflow"}
: ${SQL_USER:="airflow"}
: ${SQL_PASSWORD:="airflow"}

# Wait for the database
if [ "$1" = "webserver" ] || [ "$1" = "worker" ] || [ "$1" = "scheduler" ] ; then
  i=0
  while ! nc -z $MYSQL_HOST $MYSQL_PORT >/dev/null 2>&1 < /dev/null; do
    i=$((i+1))
    if [ "$1" = "webserver" ]; then
      echo "$(date) - waiting for ${MYSQL_HOST}:${MYSQL_PORT}... $i/$TRY_LOOP"
      if [ $i -ge $TRY_LOOP ]; then
        echo "$(date) - ${MYSQL_HOST}:${MYSQL_PORT} still not reachable, giving up"
        exit 1
      fi
    fi
    sleep 10
  done
fi

sed -i "s#sql_alchemy_conn = mysql+mysqldb://airflow:airflow@airflow-database/airflow#sql_alchemy_conn = mysql+mysqldb://$SQL_USER:$SQL_PASSWORD@$SQL_HOST:$SQL_PORT/$SQL_DATABASE#" "$AIRFLOW_HOME"/airflow.cfg

echo $SQL_HOST

$CMD initdb
