# Databook

Databook is the facebook for data. It is a dataportal, copied and designed after the descriptions of a dataportal at airbnb as per this blog post:

https://medium.com/airbnb-engineering/democratizing-data-at-airbnb-852d76c51770

The core philosophy behind databook is that users gather around data to use, consume, reorganize,
transfer, transform it and that this is a very tribal process with misinformation, leavers, new joiners.
Databook uses an automated process to extract metadata from various systems and links that together in
order to provide some clarity in that process.

In short, the dataportal keeps track how data gets created and how it is consumed in the organization
through the processing of log files, APIs, directories, metadata and other information in an automated way.

## Getting started

First the short version:

### Prerequisites

You'll need a Mac or Linux with a docker installation to run the sample deployment of databook.


There are two steps; First, build a docker container for databook locally:

```
# docker build -t gtoonstra/databook:0.1.0 .
```

Then run the docker compose file:

```
# ./run_databook.sh
```

This will download docker containers for:
- postgres
- airflow (puckel)
- elasticsearch
- neo4j

Then you can log into each respective system through these ports:

localhost:8080 (airflow)
localhost:5000 (databook)
localhost:7474 (neo4j)
localhost:9200 (elasticsearch)

Here's the long version if you run into trouble:

https://github.com/gtoonstra/databook/blob/master/docs/Installation.md

## Deployment

In a live production environment you'd set up a managed deployment of all subprojects
and probably not use the docker containers.

- A place to live for the neo4j database
- A place to live for the elasticsearch engine
- A deployment of airflow (probably can be a single vm/machine)
- A machine for the databook web app

## Built with

* Airflow
* Python
* Neo4j
* ElasticSearch
* Angular
* Bootstrap
* Flask / FlaskAdmin
* slackclient, PyGithub, ldap3

## Project layout overview

https://github.com/gtoonstra/databook/blob/master/docs/Projectlayout.md

## Contributing

Please read Contributing.md for code of conduct and the process for submitting pull requests

## Authors

* Gerard Toonstra - Initial work - [Radialmind](https://github.com/gtoonstra)

See also the list of [list of contributors](https://github.com/gtoonstra/databook/graphs/contributors)

## License 

This project is licensed under the Apache 2.0 License. See the [License](https://raw.githubusercontent.com/gtoonstra/databook/master/LICENSE) for details

## Acknowledgements

* Enormous thanks to Airbnb for describing the philosophy behind the dataportal project, the elaborate descriptions, screenshots and articles.
* Some code for LDAP authentication and initial organization of the website back-end code was heavily inspired / copied from the [airflow](https://github.com/apache/incubator-airflow) project
