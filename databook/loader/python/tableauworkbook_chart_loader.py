#!/usr/bin/python3

import logging
import os.path
from library import utils


logging.basicConfig(format='%(asctime)s - %(name)s:%(levelname)s:%(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

LOAD_CMD = """LOAD CSV WITH HEADERS FROM "file:///{0}" AS row
MERGE (workbook:Entity:Tableau:Workbook {{ name: row.workbook }})
WITH workbook, row
MATCH (chart:Entity:Tableau:Chart {{ name: row.chart }})
CALL apoc.merge.relationship(chart, row.relation, {{}}, {{}}, workbook) YIELD rel
RETURN rel
"""

utils.main(LOAD_CMD)
