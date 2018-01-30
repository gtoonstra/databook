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

from airflow.hooks.dbapi_hook import DbApiHook
from neo4j.v1 import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable


class Neo4jHook(DbApiHook):
    """
    Interact with Neo4j
    """

    conn_name_attr = 'neo4j_conn_id'
    default_conn_name = 'neo4j_default'

    def __init__(self, *args, **kwargs):
        super(Neo4jHook, self).__init__(*args, **kwargs)
        self.driver = None

    def get_conn(self):
        """
        Returns a neo4j connection object
        """
        conn = self.get_connection(self.neo4j_conn_id)

        try:
            self.driver = GraphDatabase.driver(
                "bolt://{0}:{1}".format(conn.host, conn.port),
                auth=basic_auth(conn.login, conn.password))
            self.session = self.driver.session()
            return self.session
        except ServiceUnavailable as su:
            logging.error("Neo4j is not available")
            raise

    def run(self, qry, parameters=None):
        if not self.driver:
            self.get_conn()

        try:
            data = []
            response = self.session.run(qry, parameters)
            for record in response:
                data.append(record)
            return data
        except ServiceUnavailable as su:
            logging.error("Neo4j connection error")
            raise
