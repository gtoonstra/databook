LOAD CSV WITH HEADERS FROM "file:///person_tableau_workbooks.csv" AS row
MERGE (workbook:Entity:Tableau:Workbook { name: row.workbook })
WITH workbook, row
MATCH (person:Entity:Org:Person { id: row.login })
CALL apoc.merge.relationship(person, row.relation, {}, {}, workbook) YIELD rel
RETURN rel
