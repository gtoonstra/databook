LOAD CSV WITH HEADERS FROM "file:///table_databases.csv" AS row
MERGE (database:Entity:Database:Database { name: row.database })
MERGE (table:Entity:Database:Table { name: row.name, numrows: row.numrows, database: row.database, comment: row.comment, columns: row.columns, schema: row.schema })
WITH database, table, row
CALL apoc.merge.relationship(table, row.relation, {}, {}, database) YIELD rel
RETURN rel
