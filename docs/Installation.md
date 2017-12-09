# Installation

## Install neo4j and elasticsearch

Assuming the elasticsearch API is stable, you can use the latest version of ElasticSearch.

Neo4j has restrictions on the version utilized there because it uses plugins for APOC and
a project that integrates neo4j with elasticsearch. At the time of writing I use neo4j 3.2.3. 

I used a manual install process for Debian that is described here:

https://neo4j.com/docs/operations-manual/current/installation/linux/debian/

Then use:

sudo apt-get install neo4j=3.2.3

This should complete the installation for neo4j. Check that it's working, otherwise
start its service:

> sudo service neo4j restart

Then, download 4 plugins:

- APOC for 3.2.3:

https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/3.2.3.5

- Elastic search plugins as listed on this page:

https://github.com/graphaware/neo4j-to-elasticsearch

(points to)

https://graphaware.com/products/#download_products

where you'll want:
- GraphAware Framework
- GraphAware Neo4j2Elastic
- GraphAware UUID (optional)

Modify the config of neo4j according to the instructions on the github plugin page:

https://github.com/graphaware/neo4j-to-elasticsearch

Make sure ElasticSearch is running:

> sudo service elasticsearch restart

Check: 

http://localhost:9200/

Then restart neo4j:

> sudo service neo4j restart

Check:

http://localhost:7474/browser/

You can query elasticsearch through the following:

http://localhost:9200/_cat/indices

http://localhost:9200/neo4j-index-node/_search?q=Jimmy

