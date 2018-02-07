# Installation

## Short way

Build a container locally:

```
# docker build -t gtoonstra/databook:0.1.0 .
```

Then just run it from the docker compose. There's a couple of shortcuts in that approach,
but it's the fastest way:

```
# ./run_databook.sh
```

This will download docker containers for:
- postgres
- airflow (puckel)
- elasticsearch
- neo4j

Start the containers for you and then you can log into the following apps:

localhost:8080 (airflow)
localhost:5000 (databook)
localhost:7474 (neo4j)
localhost:9200 (elasticsearch)

See the respective apps for more information.

To get started:

- From airflow, run the DAG "init_airflow", wait to finish.
- From airflow, run DAG "load_neo4j_data", wait to finish.

This will populate neo4j with some test data, transfer this to elasticsearch for
the search functionality and you can take it from there (access databook!)

### Change / contribute stuff?

See the "dag" directory where everything goes (for the moment). Change/add hooks and
operators from there.

You can add additional packages in the "requirements.txt" script in docker/airflow,
which will add some other deps you may need for additional operators.


# Long way around

Only follow this if you hate docker and you can face the pain
of neo4j version hell, elasticsearch integration and python version
incompatibility...

## Install neo4j and elasticsearch

Assuming the elasticsearch API is stable, you can use the latest version of ElasticSearch.

Neo4j has restrictions on the version utilized there because it uses plugins for APOC and
a project that integrates neo4j with elasticsearch. At the time of writing I use neo4j 3.2.3. 

I used a manual install process for Debian that is described here:

https://neo4j.com/docs/operations-manual/current/installation/linux/debian/

Then use:

sudo apt-get install neo4j=3.3.0

This should complete the installation for neo4j. Check that it's working, otherwise
start its service:

> sudo service neo4j restart

Then, download 4 plugins:

- APOC for 3.3.0:

https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases

- Elastic search plugins as listed on this page for version 3.3.1 (fixes bug in 3.3.0):

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


### Install a virtual environment

Execute setup_venv.sh:

```
# ./setup_venv.sh
```

Source the environment:

```
# source venv/bin/activate
```

Install the pip requirements:

```
# pip install -r requirements.txt
```

Start the www frontend:

```
# cd www
# python3 app.py
```

Visit http://localhost:5000/  to see the index page
