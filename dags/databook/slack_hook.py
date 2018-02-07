from slackclient import SlackClient
from airflow.hooks.base_hook import BaseHook
from airflow.exceptions import AirflowException


class DatabookSlackHook(BaseHook):
    """
       Interact with Slack, using slackclient library.
    """

    def __init__(self, token=None, slack_conn_id=None):
        """
        Takes both Slack API token directly and connection that has Slack API token.

        If both supplied, Slack API token will be used.

        :param token: Slack API token
        :type token: string
        :param slack_conn_id: connection that has Slack API token in the password field
        :type slack_conn_id: string
        """
        self.token = self.__get_token(token, slack_conn_id)

    def __get_token(self, token, slack_conn_id):
        if token is not None:
            return token
        elif slack_conn_id is not None:
            conn = self.get_connection(slack_conn_id)

            if not getattr(conn, 'password', None):
                raise AirflowException('Missing token(password) in Slack connection')
            return conn.password
        else:
            raise AirflowException('Cannot get token: No valid Slack token nor slack_conn_id supplied.')

    def call(self, method, api_params):
        sc = SlackClient(self.token)
        rc = sc.api_call(method, **api_params)

        if not rc['ok']:
            msg = "Slack API call failed ({0})".format(rc['error'])
            raise AirflowException(msg)

        return rc
