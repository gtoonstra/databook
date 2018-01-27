from neo4j.v1 import GraphDatabase, basic_auth

driver = GraphDatabase.driver("bolt://127.0.0.1:7687", auth=basic_auth("neo4j", "blade1"))



class Neo4JService(object):
    def __init__(self):
        self.session = driver.session()

    def query(self, qry, params):
        data = []
        response = self.session.run(qry, params)
        for record in response:
            data.append(record)
        return data
