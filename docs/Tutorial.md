# Tutorial

### Quick start

There are some test files that you can use to verify the functioning of databook
and for demo purposes.

1. Make sure you followed all the steps to install elasticsearch and neo4j and that these are working
2. Start the www frontend (by default, it starts at port 5000). There is no authentication yet.
3. From the "loader" directory, look into the tests/resources directory.
4. Copy the .csv files to the neo4j import directory. On Ubuntu, this is probably "/var/lib/neo4j/import". On OSX, you can run neo4j on the console, then it will be where you installed it.
5. In "loader/tests", execute the "load_all.sh" script. This will import the CSV files.
6. Go to "http://localhost:5000", then search for user "Data Book" to get you started.

This process should have imported all the data into neo4j. The elasticsearch plugin should synchronize that
with elasticsearch, so you can search the neo4j "nodes" from the search box in the front end.

### Loading your own data

See the _processing_ directory for examples how to generate CSV files, which you can then load into the database.

In the _table_table_ subdirectory, you'll find a process that generates the table-level lineage files.
These describe which tables derive from other tables.

Run it like this:

```
python3 main.py --sqldir resources/ --outfile table_table.csv
```

Then verify the contents of the _table_table.csv_ file.
