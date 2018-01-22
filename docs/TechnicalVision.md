Technical Vision
================

Databook is primarily a web application which interacts with a graph database to
retrieve data. This document describes the high level technical vision for the project.

Deployment
==========

Right now databook is installable in a python virtual environment through a pip package.
It would be much better for now if the databook solution could be deployed as a set of
docker containers in a docker-compose operation. Airflow can be deployed on the site as 
the solution to populate the database and manage the overall solution.

User interface
==============

The user interface is currently built using a mix of responsive ajax-like behavior
with server-side rendered pages. The responsive UI is built using Angular, the server
side rendering is done on Flask with help of FlaskAdmin. An important attribute of 
the system are "permalinks". This allows people to share URLs in the first place on
social media and they can be recorded in other systems and continue to function.

Loading process
===============

The system needs data as input before it can be useful. The data queried exists in a 
graph database, which gets loaded through a set of simple CSV files.

These CSV files need to be generated and as of now this is done through a set of manually
run scripts. It would be better if these files would be generated through a DAG workflow
in airflow.

This image demonstrates the sources of the CSV files and where the data comes from:

![Extracting data](https://github.com/gtoonstra/databook/blob/master/docs/images/extracting_data.jpeg "Data extraction design")
