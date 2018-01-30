LOAD CSV WITH HEADERS FROM "file:///tableau_charts_workbook.csv" AS row
MERGE (workbook:Entity:Tableau:Workbook { name: row.workbook })
WITH workbook, row
MATCH (chart:Entity:Tableau:Chart { name: row.chart })
CALL apoc.merge.relationship(chart, row.relation, {}, {}, workbook) YIELD rel
RETURN rel
