# Project layout

Databook has the following directories, which have the following purposes:

|directory|purpose|
|---------|-------|
|docs|Documentation|
|dags|Airflow dag code for extracting data from API's, munge them and get them ready for neo4j import|
|docker|Mostly configuration files and host mounted directories for use with dependent docker containers|
|databook|Some logic code for the backend of the website|
|databook/www|The website of databook (angular, bootstrap)|
