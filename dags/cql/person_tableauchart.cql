LOAD CSV WITH HEADERS FROM "file:///person_tableau_charts.csv" AS row
MERGE (chart:Entity:Tableau:Chart { name: row.chart })
WITH chart, row
MATCH (person:Entity:Org:Person { id: row.login })
CALL apoc.merge.relationship(person, row.relation, {}, {}, chart) YIELD rel
RETURN rel
