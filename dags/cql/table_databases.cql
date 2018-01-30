LOAD CSV WITH HEADERS FROM "file:///table_databases.csv" AS row
MERGE (database:Entity:Database:Database { name: row.database })
MERGE (table:Entity:Database:Table { name: row.table, numrows: row.numrows, database: row.database })
MERGE (person:Entity:Org:Person { id: row.creator })
WITH database, table, person, row
CALL apoc.merge.relationship(table, row.relation, {}, {}, database) YIELD rel
WITH database, table, person, row
CALL apoc.merge.relationship(person, "CREATED", {}, {}, table) YIELD rel
RETURN rel
