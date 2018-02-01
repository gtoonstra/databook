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

from airflow.hooks.dbapi_hook import BaseHook
from ldap3 import Server, Connection, ALL
from future.utils import native
import logging


class LdapHook(BaseHook):
    """
    Interact with Ldap
    """

    def __init__(
        self, 
        ldap_conn_id='ldap_default',
        *args, **kwargs):
        self.ldap_conn_id = ldap_conn_id

    def get_conn(self):
        """
        Returns an LDAP connection object
        """
        logging.info("Connecting to {0}".format(self.ldap_conn_id))
        conn = self.get_connection(self.ldap_conn_id)
        url = 'ldap://{0}:{1}'.format(conn.host, conn.port)

        server = Server(url, get_info=ALL)
        conn = Connection(server, 
            native(conn.login),
            native(conn.password))

        if not conn.bind():
            logging.error("Cannot bind to ldap server: %s ", conn.last_error)
            raise Exception("Cannot bind to ldap server")

        return conn

    def run(self, base, search_filter, attributes, member_of_string):
        conn = self.get_conn()

        result = []
        searchParameters = { 'search_base': base,
                             'search_filter': search_filter,
                             'attributes': attributes}
        conn.search(**searchParameters)
        for entry in conn.entries:
            d = {}
            d['dn'] = entry.entry_dn
            for attr in attributes:
                if attr == 'memberOf':
                    if isinstance(entry[attr].value, list):
                        d[attr] = entry[attr].value
                    else:
                        d[attr] = []
                else:
                    d[attr] = entry[attr].value
            result.append(d)

        return result
