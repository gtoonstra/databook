#!/usr/bin/python3

import logging
import os.path
from library import utils


logging.basicConfig(format='%(asctime)s - %(name)s:%(levelname)s:%(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

LOAD_CMD = """LOAD CSV WITH HEADERS FROM "file:///{0}" AS row
MERGE (group:Entity:Org:Group {{ name: row.group }})
WITH group, row
MATCH (person:Entity:Org:Person {{ id: row.login }})
CALL apoc.merge.relationship(person, row.relation, {{}}, {{}}, group) YIELD rel
RETURN rel
"""

utils.main(LOAD_CMD)
