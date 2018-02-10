LOAD CSV WITH HEADERS FROM "file:///persons.csv" AS row
MERGE (person:Entity:Org:Person {
    id: row.login,
    email: row.email,
    name: row.name,
    role: row.role,
    slack: row.slack,
    github: row.github,
    github_url: row.github_url,
    location: row.location
})
