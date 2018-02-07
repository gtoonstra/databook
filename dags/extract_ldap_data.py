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
import json
from datetime import datetime, timedelta
from airflow import models
from airflow.settings import Session
from databook.operators import LdapOperator
from airflow.operators.python_operator import PythonOperator
from databook.operators import FileCopyOperator
from databook.operators import SlackAPIUserListOperator
from databook.operators import GithubUserListOperator


args = {
    'owner': 'airflow',
    'start_date': airflow.utils.dates.days_ago(1),
    'provide_context': True
}

PERSON_FILE = '/tmp/persons.json'
GROUP_FILE = '/tmp/groups.json'
FLATTENED_GROUP_FILE = '/tmp/flattened_groups.json'
PERSON_FILE_CSV = '/tmp/persons.csv'
PERSON_GROUPS_FILE_CSV = '/tmp/person_groups.csv'
SLACK_FILE_JSON = '/tmp/slack.json'
GITHUB_FILE_JSON = '/tmp/github.json'

dag = airflow.DAG(
    'extract_neo4j_data',
    schedule_interval="@daily",
    default_args=args,
    max_active_runs=1)

ldap_persons = LdapOperator(
    task_id='person_extract',
    ldap_conn_id='freeipa_ldap',
    base='dc=demo1,dc=freeipa,dc=org',
    search_filter='(objectClass=person)',
    attributes=['cn', 'sn', 'uid', 'mail', 'manager', 'displayName', 'memberOf'],
    file_path=PERSON_FILE,
    member_of_string=',cn=groups,',
    dag=dag)

ldap_groups = LdapOperator(
    task_id='group_extract',
    ldap_conn_id='freeipa_ldap',
    base='dc=demo1,dc=freeipa,dc=org',
    search_filter='(objectClass=posixgroup)',
    attributes=['cn', 'displayName', 'description', 'memberOf'],
    file_path=GROUP_FILE,
    member_of_string=',cn=groups,',
    dag=dag)


def flatten_groups(ds, **kwargs):
    group_list = None
    with open(GROUP_FILE, 'r') as infile:
        group_list = json.load(infile)

    groups = {}
    for item in group_list:
        groups[item['dn']] = item

    flattened_memberships = {}
    for k, group in groups.items():
        list_of_groups = flattened_memberships.get(k, set([]))

        if not group['memberOf']:
            flattened_memberships[k] = []
            continue

        for member_group in group['memberOf']:
            list_of_groups.add(member_group)
            subgroup = groups.get(member_group)
            if subgroup:
                for sub_subgroup in subgroup['memberOf']:
                    if sub_subgroup in groups:
                        list_of_groups.add(sub_subgroup)

        flattened_memberships[k] = list(list_of_groups)

    with open(FLATTENED_GROUP_FILE, 'w') as outfile:
        json.dump(flattened_memberships, outfile)


def write_csvs(ds, **kwargs):
    flattened_groups = None
    groups = {}
    persons = None
    with open(PERSON_FILE, 'r') as infile:
        persons = json.load(infile)
    with open(GROUP_FILE, 'r') as infile:
        group_list = json.load(infile)
        for item in group_list:
            groups[item['dn']] = item
    with open(FLATTENED_GROUP_FILE, 'r') as infile:
        flattened_groups = json.load(infile)

    slack_users = {}
    with open(SLACK_FILE_JSON, 'r') as slackfile:
        # name,fullname,title,displayname,email,firstname,lastname,image_url
        for line in slackfile:
            line = line.strip()
            user = json.loads(line)

            print(user)

            slack_users[user['email']] = user

    with open(PERSON_FILE_CSV, 'w') as person_file:
        person_file.write('login,email,name,role,slack,github,location\n')
        with open(PERSON_GROUPS_FILE_CSV, 'w') as groups_file:
            groups_file.write('login,relation,group\n')
            for person in persons:
                if person['mail'] in slack_users:
                    slack_user = slack_users[person['mail']]
                else:
                    slack_user = {
                        'title': 'unknown',
                        'name': person['uid']
                    }

                # login,email,name,role,slack,github,location
                person_rec = '{0},{1},{2},{3},{4},{5},{6}\n'.format(
                    person['uid'],
                    person['mail'],
                    person['displayName'],
                    slack_user['title'],
                    slack_user['name'],
                    'github',
                    'location')

                person_file.write(person_rec)
                for group in person['memberOf']:
                    if group not in groups:
                        continue
                    group_obj = groups[group]
                    group_rec = '{0},ASSOCIATED,{1}\n'.format(
                        person['uid'],
                        group_obj['cn'])
                    groups_file.write(group_rec)

                    # login,relation,group
                    if group in flattened_groups:
                        members = flattened_groups[group]
                        for member in members:
                            if member not in groups:
                                continue
                            group_rec = '{0},ASSOCIATED,{1}\n'.format(
                                person['uid'],
                                groups[member]['cn'])
                            groups_file.write(group_rec)


flatten_groups = PythonOperator(
    task_id='flatten_groups',
    python_callable=flatten_groups,
    dag=dag)

write_csvs = PythonOperator(
    task_id='write_csvs',
    python_callable=write_csvs,
    dag=dag)

copy_persons = FileCopyOperator(
    task_id='copy_persons',
    source_path=PERSON_FILE_CSV,
    target_path='/import/persons.csv',
    dag=dag)

copy_person_groups = FileCopyOperator(
    task_id='copy_person_groups',
    source_path=PERSON_GROUPS_FILE_CSV,
    target_path='/import/person_groups.csv',
    dag=dag)

extract_slack = SlackAPIUserListOperator(
    task_id='extract_slack_users',
    slack_conn_id='slack_conn',
    method='users.list',
    output_file=SLACK_FILE_JSON,
    dag=dag)

extract_github = GithubUserListOperator(
    task_id='extract_github_users',
    github_conn_id='github_conn',
    output_file=GITHUB_FILE_JSON,
    organization_id='<your-org>',
    dag=dag)


ldap_persons >> flatten_groups
ldap_groups >> flatten_groups
flatten_groups >> write_csvs
extract_slack >> write_csvs
extract_github >> write_csvs
write_csvs >> copy_persons
write_csvs >> copy_person_groups
