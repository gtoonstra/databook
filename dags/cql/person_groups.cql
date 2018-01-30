LOAD CSV WITH HEADERS FROM "file:///person_groups.csv" AS row
MERGE (group:Entity:Org:Group { name: row.group })
WITH group, row
MATCH (person:Entity:Org:Person { id: row.login })
CALL apoc.merge.relationship(person, row.relation, {}, {}, group) YIELD rel
RETURN rel
