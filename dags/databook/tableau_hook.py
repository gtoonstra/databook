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
import tableauserverclient as TSC
import logging


class TableauHook(DbApiHook):
    """
    Interact with Tableau
    """
    conn_name_attr = 'tableau_conn_id'
    default_conn_name = 'tableau_default'

    def __init__(self, *args, **kwargs):
        super(TableauHook, self).__init__(*args, **kwargs)

    def get_conn(self):
        """
        Returns a neo4j connection object
        """
        conn = self.get_connection(self.tableau_conn_id)
        tableau_auth = TSC.TableauAuth(conn.login, conn.password)
        server = TSC.Server('http://{0}:{1}'.format(conn.host, conn.port))
        logged_in = ''
        try:
            logged_in = server.auth.sign_in(tableau_auth)
        except Exception as e:
            logging.error("Failed to log into tableau server")
            logging.error(e)
            raise

        return server
