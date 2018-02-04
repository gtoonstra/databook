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
from databook.ldap_hook import LdapHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
import logging
import json
from shutil import copyfile


class Neo4jOperator(BaseOperator):
    """
    Executes Cypher code against a Neo4j database

    :param neo4j_conn_id: reference to a specific Neo4j database
    :type neo4j_conn_id: string
    :param cql: the cypher ql code to be executed
    :type cql: Can receive a str representing a cql statement,
        a list of str (cql statements), or reference to a template file.
        Template reference are recognized by str ending in '.sql'
    """

    template_fields = ('cql',)
    template_ext = ('.cql',)
    ui_color = '#ededed'

    @apply_defaults
    def __init__(
            self,
            cql,
            neo4j_conn_id='neo4j_default',
            parameters=None, *args, **kwargs):
        super(Neo4jOperator, self).__init__(*args, **kwargs)
        self.neo4j_conn_id = neo4j_conn_id
        self.cql = cql
        self.parameters = parameters

    def execute(self, context):
        logging.info('Executing: %s', self.cql)
        hook = Neo4jHook(neo4j_conn_id=self.neo4j_conn_id)
        hook.run(
            self.cql,
            parameters=self.parameters)


class LdapOperator(BaseOperator):
    """
    Executes a search against an LDAP store and stores the results in a file.

    :param base: Base LDAP hierarchy to check
    :type base: string
    :param search_filter: LDAP objects to filter on
    :type search_filter: string
    :param attributes: List of string attributes to extract in the query
    :type attributes: list
    """

    ui_color = '#ededed'

    @apply_defaults
    def __init__(
            self,
            base,
            search_filter, 
            attributes,
            file_path,
            member_of_string=None,
            ldap_conn_id='ldap_default',
            parameters=None,
            *args, **kwargs):
        super(LdapOperator, self).__init__(*args, **kwargs)
        self.ldap_conn_id = ldap_conn_id
        self.base = base
        self.search_filter = search_filter
        self.attributes = attributes
        self.file_path = file_path
        self.member_of_string = member_of_string

    def execute(self, context):
        logging.info('Executing search on {0}'.format(self.ldap_conn_id))
        hook = LdapHook(ldap_conn_id=self.ldap_conn_id)
        result = hook.run(
            self.base, 
            self.search_filter, 
            self.attributes,
            self.member_of_string)
        with open(self.file_path, 'w') as outfile:
            json.dump(result, outfile)


class FileCopyOperator(BaseOperator):
    """
    Copies a file on the mapped file system

    :param source_path: Source where file is located
    :type source_path: string
    :param target_path: Destination for the file
    :type target_path: string
    """

    ui_color = '#ededed'

    @apply_defaults
    def __init__(
            self,
            source_path,
            target_path,
            *args, **kwargs):
        super(FileCopyOperator, self).__init__(*args, **kwargs)
        self.source_path = source_path
        self.target_path = target_path

    def execute(self, context):
        copyfile(self.source_path, self.target_path)
