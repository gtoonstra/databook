import sqlineage
from lineage import LineageModel
import argparse
import sys
import os
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

root = None
lastModelAtLevel = {}


def callback(parent, table, alias, query_alias, joins, operation, level):
    """
    Callback from the scanner, which is where you add the SQL blocks
    to your lineage model
    """
    global root

    if alias == 'ROOT':
        root = LineageModel(operation)
        root.table = table
        root.alias = alias
        if (len(joins) > 0):
            root.joins = joins
        root.query_alias = query_alias
        root.level = level
        lastModelAtLevel[level] = root
    else:
        model = LineageModel(operation)
        model.table = table
        model.alias = alias
        if (len(joins) > 0):
            model.joins = joins
        model.query_alias = query_alias
        if alias != 'ROOT':
            parent_model = lastModelAtLevel[level-1]
            parent_model.connect_model(model)
        lastModelAtLevel[level] = model


def process_file(dirpath, filename, sql_preprocessor):
    """
    Processes a single file from the directory
    """
    abs_path = os.path.join(dirpath, filename)
    logger.info("Processing {0}".format(abs_path))
    try:
        with open(abs_path, 'r') as infile:
            sql = infile.read()
            sql = sql_preprocessor(sql, dirpath, filename)
            sqlineage.scan(sql, callback)
    except UnicodeDecodeError as e:
        logger.error(e)
        pass


def preprocess_sql(sql, dirpath, filename):
    """
    For site-specific processing of SQL file content;
    Sometimes SQL files have comments that get replaced by other statements
    in code. This is where you can replicate that.
    """
    return sql


def extract_table_and_db(full_table_name, default_db):
    """
    Extract the database and table name from a table identifier
    """
    if default_db is None:
        default_db = 'unknown'

    identifiers = full_table_name.split(".")
    if len(identifiers) < 3:
        return identifiers[-1], default_db
    if len(identifiers) == 3:
        return identifiers[2], identifiers[0]
    if len(identifiers) == 4:
        return identifiers[3], identifiers[1]


def process_relationships(fout, root, dirpath, filename):
    """
    Processes the relationships between tables
    """
    if root is None:
        return

    # transaction_margin,dwh,CONSUMED,sold_quantity,dwh
    source_db = None
    dest_db = None

    logger.info(root)
    insert_tables, select_tables = root.collect_tables()

    if len(insert_tables) == 0:
        logger.error("Missing insert statements at: {0}".format(filename))
        return

    insert_table, insert_db = extract_table_and_db(insert_tables[0], dest_db)
    for table in select_tables:
        select_table, select_db = extract_table_and_db(table, source_db)
        if select_table is None or len(select_table) == 0:
            continue
        elems = [insert_table.lower()]
        elems.append(insert_db.lower())
        elems.append('CONSUMED')
        elems.append(select_table.lower())
        elems.append(select_db.lower())
        line = ",".join(elems)
        fout.write(line)
        fout.write("\n")


parser = argparse.ArgumentParser(description='Process a directory of SQL files')
parser.add_argument('--sqldir', help='Directory to find SQL files in.')
parser.add_argument('--outfile', help='Output file (CSV)')

args = parser.parse_args()
if args.sqldir is None:
    logger.error('Directory is mandatory.')
    parser.print_help()
    sys.exit(-1)

if not os.path.isdir(args.sqldir):
    logger.error('That is not a directory.')
    parser.print_help()
    sys.exit(-1)

if args.outfile is None:
    logger.error('Output file setting is required.')
    parser.print_help()
    sys.exit(-1)

out_file = os.path.expanduser(args.outfile)
out_dir = os.path.dirname(out_file)

if len(out_dir) > 0 and not os.path.isdir(out_dir):
    logger.error('Output directory does not exist')
    parser.print_help()
    sys.exit(-1)


fout = open(out_file, 'wt')
fout.write('table1,database1,relation,table2,database2\n')

for dirpath, dnames, fnames in os.walk(args.sqldir):
    for filename in fnames:
        if filename.endswith(".sql"):
            root = None
            lastModelAtLevel = {}

            process_file(dirpath, filename, preprocess_sql)
            process_relationships(fout, root, dirpath, filename)

fout.flush()
fout.close()
