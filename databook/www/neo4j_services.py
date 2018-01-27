from neo4j.v1 import GraphDatabase, basic_auth
from databook.utils.logging_mixin import LoggingMixin
from databook.exceptions import DatabookException


log = LoggingMixin().log


class Neo4JService(object):
    def __init__(self):
        self.connected = False
        self.attempts = 0

    def connect(self):
        neo4j_url = conf.get('graphdb', 'neo4j_url')
        neo4j_user = conf.get('graphdb', 'neo4j_user')
        neo4j_pass = conf.get('graphdb', 'neo4j_pass')

        if self.attempts > 10:
            raise DatabookException("Attempted to connect > 10 times")

        try:
            driver = GraphDatabase.driver(neo4j_url, auth=basic_auth(neo4j_user, neo4j_pass))
            self.session = driver.session()
            self.connected = True
            self.attempts = 0
        except neo4j.exceptions.ServiceUnavailable as su:
            log.error("Neo4j is not available")
            self.connected = False
            self.attempts += 1

    def query(self, qry, params):
        if not self.connected:
            self.connect()

        data = []
        response = self.session.run(qry, params)
        for record in response:
            data.append(record)
        return data
