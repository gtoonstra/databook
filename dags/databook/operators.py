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
from databook.slack_hook import DatabookSlackHook
from databook.github_hook import GithubHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
import logging
import json
import time
import codecs
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


def remove_commas(txt):
    if txt is None:
        return ''
    return txt.replace(',', ';')


class SlackAPIUserListOperator(BaseOperator):
    """
    Iterates through a user list and writes result to disk
    """

    ui_color = '#FFBA40'

    @apply_defaults
    def __init__(self,
                 slack_conn_id,
                 method,
                 output_file,
                 member_filter=None,
                 limit=20,
                 *args, **kwargs):
        super(SlackAPIUserListOperator, self).__init__(*args, **kwargs)
        self.method = method
        self.member_filter = member_filter
        self.limit = limit
        self.cursor = None
        self.output_file = output_file
        self.slack_conn_id = slack_conn_id

    def construct_api_call_params(self):
        self.api_params = {
            'limit': self.limit
        }
        if self.cursor is not None:
            self.api_params['cursor'] = self.cursor

    def execute(self, **kwargs):
        slack = DatabookSlackHook(slack_conn_id=self.slack_conn_id)

        has_more = True
        ctr = 0

        with codecs.open(self.output_file, 'w', encoding='utf-8') as outfile:
            while has_more:
                ctr += 1

                self.construct_api_call_params()
                result = slack.call(self.method, self.api_params)
                if not result['ok']:
                    raise Exception(result['error'])

                self.cursor = result['response_metadata']['next_cursor']
                if self.cursor == '':
                    has_more = False 

                for member in result['members']:
                    if member['is_bot'] or not 'email' in member['profile']:
                        continue
                    if member['deleted']:
                        continue

                    if self.member_filter:
                        if not self.member_filter(member):
                            continue
                    
                    profile = member['profile']
                    user = {
                        "name": remove_commas(member['name']),
                        "real_name": remove_commas(profile['real_name']),
                        "title": remove_commas(profile['title']),
                        "display_name": remove_commas(profile['display_name']),
                        "email": remove_commas(profile['email']),
                        "first_name": remove_commas(profile.get('first_name', '')),
                        "last_name": remove_commas(profile.get('last_name', '')),
                        "profile_photo": remove_commas(profile['image_192'])
                    }
                    outfile.write(json.dumps(user))
                    outfile.write('\n')

                time.sleep(10)

                if ctr > 2:
                    has_more = False


class GithubUserListOperator(BaseOperator):
    """
    Get github usernames in an organization and dump to disk
    """

    ui_color = '#FFBA40'

    @apply_defaults
    def __init__(self,
                 github_conn_id,
                 output_file,
                 organization_id,
                 member_filter=None,
                 *args, **kwargs):
        super(GithubUserListOperator, self).__init__(*args, **kwargs)
        self.member_filter = member_filter
        self.output_file = output_file
        self.organization_id = organization_id
        self.github_conn_id = github_conn_id

    def execute(self, **kwargs):
        hook = GithubHook(github_conn_id=self.github_conn_id)
        g = hook.get_conn()
        org = g.get_organization(self.organization_id)
        with codecs.open(self.output_file, 'w', encoding='utf-8') as outfile:
            for member in org.get_members():
                user = {
                    "name": remove_commas(member.name),
                    "login": remove_commas(member.login),
                    "email": remove_commas(member.email),
                    "url": remove_commas(member.url),
                    "location": remove_commas(member.location)
                }
                outfile.write(json.dumps(user))
                outfile.write('\n')
