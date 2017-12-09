from neo4j.v1 import GraphDatabase, basic_auth
import logging
import argparse


logger = logging.getLogger(__name__)
driver = None

def get_session(clear=False):
    # THe graphdatabase driver must be kept at global level, 
    # because there's a finalizer that closes all connections if it 
    # goes out of scope
    global driver

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "blade1"))
    session = driver.session()

    if clear:
        logger.info("Clearing the database first")
        session.run("MATCH (n)\n"
            "OPTIONAL MATCH (n)-[r]-()\n"
            "DELETE n,r")

    return session

def process_file(session, loadcmd, filename):
    loadcmd = loadcmd.format(filename)
    session.run(loadcmd)

def main(loadcmd):
    parser = argparse.ArgumentParser(description='Load a file into a neo4j database.')
    parser.add_argument('--clear', action='store_true', dest='clear', help='Delete database prior to the load')
    parser.add_argument('files', metavar='file', type=str, nargs='+', help='List of files to load')
    args = parser.parse_args()

    session = get_session(args.clear)

    for filename in args.files:
        process_file(session, loadcmd, filename)

    session.close()
