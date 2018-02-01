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
from databook.operators import Neo4jOperator
from airflow import models
from airflow.settings import Session


args = {
    'owner': 'airflow',
    'start_date': airflow.utils.dates.days_ago(1),
    'provide_context': True
}


dag = airflow.DAG(
    'load_neo4j_data',
    schedule_interval="@daily",
    default_args=args,
    max_active_runs=1)

trunc_db = Neo4jOperator(
    task_id='trunc_db',
    neo4j_conn_id='neo4j',
    cql='MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r',
    dag=dag)

persons = Neo4jOperator(
    task_id='persons',
    neo4j_conn_id='neo4j',
    cql='cql/persons.cql',
    dag=dag)

person_groups = Neo4jOperator(
    task_id='person_groups',
    neo4j_conn_id='neo4j',
    cql='cql/person_groups.cql',
    dag=dag)

person_tbchart = Neo4jOperator(
    task_id='person_tbchart',
    neo4j_conn_id='neo4j',
    cql='cql/person_tableauchart.cql',
    dag=dag)

person_tbwb = Neo4jOperator(
    task_id='person_tbwb',
    neo4j_conn_id='neo4j',
    cql='cql/person_tableauwb.cql',
    dag=dag)

table_dbs = Neo4jOperator(
    task_id='table_dbs',
    neo4j_conn_id='neo4j',
    cql='cql/table_databases.cql',
    dag=dag)

table_table = Neo4jOperator(
    task_id='table_table',
    neo4j_conn_id='neo4j',
    cql='cql/table_table.cql',
    dag=dag)

tbchart_table = Neo4jOperator(
    task_id='tbchart_table',
    neo4j_conn_id='neo4j',
    cql='cql/tableauchart_table.cql',
    dag=dag)

tbwb_chart = Neo4jOperator(
    task_id='tbwb_chart',
    neo4j_conn_id='neo4j',
    cql='cql/tableauwb_chart.cql',
    dag=dag)

trunc_db >> persons
persons >> person_groups >> person_tbwb >> person_tbchart
person_tbchart >> table_dbs >> table_table
table_table >> tbchart_table >> tbwb_chart

