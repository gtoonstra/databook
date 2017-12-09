#!/usr/bin/python3

import logging
import os.path
from library import utils


logging.basicConfig(format='%(asctime)s - %(name)s:%(levelname)s:%(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

LOAD_CMD = """LOAD CSV WITH HEADERS FROM "file:///{0}" AS row
MERGE (person:Entity:Org:Person {{ id: row.login, email: row.email, name: row.name, role: row.role, slack: row.slack, github: row.github, location: row.location}})
"""

utils.main(LOAD_CMD)
