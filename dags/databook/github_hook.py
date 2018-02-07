from airflow.hooks.base_hook import BaseHook
from airflow.exceptions import AirflowException
from github import Github


class GithubHook(BaseHook):
    """
       Interact with github
    """

    def __init__(self, github_conn_id):
        self.token = self.__get_token(github_conn_id)

    def __get_token(self, github_conn_id):
        conn = self.get_connection(github_conn_id)

        if not getattr(conn, 'password', None):
            raise AirflowException('Missing token(password) in Slack connection')
        return conn.password

    def get_conn(self):
        g = Github(self.token)
        return g
