#!/usr/bin/python3

import logging
import os.path
from library import utils


logging.basicConfig(format='%(asctime)s - %(name)s:%(levelname)s:%(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

LOAD_CMD = """LOAD CSV WITH HEADERS FROM "file:///{0}" AS row
MERGE (database:Entity:Database:Database {{ name: row.database }})
MERGE (table:Entity:Database:Table {{ name: row.table, numrows: row.numrows, database: row.database }})
MERGE (person:Entity:Org:Person {{ id: row.creator }})
WITH database, table, person, row
CALL apoc.merge.relationship(table, row.relation, {{}}, {{}}, database) YIELD rel
WITH database, table, person, row
CALL apoc.merge.relationship(person, "CREATED", {{}}, {{}}, table) YIELD rel
RETURN rel
"""

utils.main(LOAD_CMD)
