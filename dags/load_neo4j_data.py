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
    'start_date': airflow.utils.dates.days_ago(7),
    'provide_context': True
}


dag = airflow.DAG(
    'load_neo4j_data',
    schedule_interval="@daily",
    default_args=args,
    max_active_runs=1)

t1 = Neo4jOperator(task_id='load_persons',
                   neo4j_conn_id='neo4j',
                   cypher='test',
                   provide_context=False,
                   dag=dag)
