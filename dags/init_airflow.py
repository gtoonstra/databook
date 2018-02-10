# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import airflow
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
from airflow import models
from airflow.settings import Session
import logging


args = {
    'owner': 'airflow',
    'start_date': airflow.utils.dates.days_ago(7),
    'provide_context': True
}


def init_airflow_databook():
    logging.info('Creating connections')

    session = Session()

    def create_new_conn(session, attributes):
        conn_id = attributes.get("conn_id")
        new_conn = session.query(models.Connection).filter(models.Connection.conn_id==conn_id).first()
        if not new_conn:
            logging.info("No connection found")
            new_conn = models.Connection()
        new_conn.conn_id = conn_id
        new_conn.conn_type = attributes.get('conn_type')
        new_conn.host = attributes.get('host')
        new_conn.port = attributes.get('port')
        new_conn.schema = attributes.get('schema')
        new_conn.login = attributes.get('login')
        new_conn.set_password(attributes.get('password'))

        session.merge(new_conn)
        session.commit()

    create_new_conn(session,
                    {"conn_id": "neo4j",
                     "conn_type": "bolt",
                     "host": "neo4j_databook",
                     "port": 7687,
                     "schema": "",
                     "login": "neo4j",
                     "password": "j4oen"})

    create_new_conn(session,
                    {"conn_id": "ldap_conn",
                     "conn_type": "ldap",
                     "host": "ipa.demo1.freeipa.org",
                     "port": 389,
                     "schema": "",
                     "login": "uid=admin,cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org",
                     "password": "Secret123"})

    session.close()

dag = airflow.DAG(
    'init_airflow_databook',
    schedule_interval="@once",
    default_args=args,
    max_active_runs=1)

t1 = PythonOperator(task_id='init_airflow_databook',
                    python_callable=init_airflow_databook,
                    provide_context=False,
                    dag=dag)
