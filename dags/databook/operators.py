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

from databook.neo4j_hook import Neo4jHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
import logging


class Neo4jOperator(BaseOperator):
    """
    Executes Cypher code against a Neo4j database

    :param oracle_conn_id: reference to a specific Oracle database
    :type oracle_conn_id: string
    :param sql: the sql code to be executed
    :type sql: Can receive a str representing a sql statement,
        a list of str (sql statements), or reference to a template file.
        Template reference are recognized by str ending in '.sql'
    """

    template_fields = ('cypher',)
    ui_color = '#ededed'

    @apply_defaults
    def __init__(
            self, 
            cypher, 
            neo4j_conn_id='neo4j_default', 
            parameters=None, *args, **kwargs):
        super(Neo4jOperator, self).__init__(*args, **kwargs)
        self.neo4j_conn_id = neo4j_conn_id
        self.cypher = cypher
        self.parameters = parameters

    def execute(self, context):
        logging.info('Executing: %s', self.cypher)
        hook = Neo4jHook(neo4j_conn_id=self.neo4j_conn_id)
        hook.run(
            self.cypher,
            parameters=self.parameters)
