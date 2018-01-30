LOAD CSV WITH HEADERS FROM "file:///table_table.csv" AS row
MERGE (table1:Entity:Database:Table { name: row.table1, database: row.database1 })
MERGE (table2:Entity:Database:Table { name: row.table2, database: row.database2 })
WITH table1, table2, row
CALL apoc.merge.relationship(table1, row.relation, {}, {}, table2) YIELD rel
RETURN rel
