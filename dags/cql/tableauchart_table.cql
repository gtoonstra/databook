LOAD CSV WITH HEADERS FROM "file:///tableauchart_table.csv" AS row
WITH row
MATCH (table:Entity:Database:Table { name: row.table, database: row.database })
MATCH (chart:Entity:Tableau:Chart { name: row.chart })
CALL apoc.merge.relationship(chart, row.relation, {}, {}, table) YIELD rel
RETURN rel
