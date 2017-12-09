#!/usr/bin/python3

import logging
import os.path
from library import utils


logging.basicConfig(format='%(asctime)s - %(name)s:%(levelname)s:%(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

LOAD_CMD = """LOAD CSV WITH HEADERS FROM "file:///{0}" AS row
MERGE (table1:Entity:Database:Table {{ name: row.table1, database: row.database1 }})
MERGE (table2:Entity:Database:Table {{ name: row.table2, database: row.database2 }})
WITH table1, table2, row
CALL apoc.merge.relationship(table1, row.relation, {{}}, {{}}, table2) YIELD rel
RETURN rel
"""

utils.main(LOAD_CMD)
