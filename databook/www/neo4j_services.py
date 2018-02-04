from neo4j.v1 import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable
from databook.utils.logging_mixin import LoggingMixin
from databook.exceptions import DatabookException
from databook import configuration as conf


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
            log.info("Connecting {0} {1} {2}".format(neo4j_url, neo4j_user, neo4j_pass))
            self.driver = GraphDatabase.driver(neo4j_url, auth=basic_auth(neo4j_user, neo4j_pass))
            session = self.driver.session()
            self.connected = True
            self.attempts = 0
            return session
        except ServiceUnavailable as su:
            log.error("Neo4j is not available")
            self.connected = False
            self.attempts += 1
            raise

    def query(self, qry, params):
        if not self.connected:
            self.session = self.connect()

        try:
            data = []
            response = self.session.run(qry, params)
            for record in response:
                data.append(record)
            return data
        except ServiceUnavailable as su:
            log.error("Neo4j connection error")
            self.connected = False
            self.attempts = 0
            raise
