# Neo4j and Cypher

## Introduction to Neo4j

Neo4j is a graph database that stores data as nodes and relationships, enabling efficient queries over complex relationships.

## Basic Concepts

### Nodes

Represent entities in the graph:

```cypher
(:Person {name: "Alice"})
(:Document {title: "Introduction"})
```

### Relationships

Connect nodes:

```cypher
(:Person)-[:KNOWS]->(:Person)
(:Document)-[:CONTAINS]->(:Page)
```

### Properties

Both nodes and relationships can have properties:

```cypher
(:Person {name: "Alice", age: 30})
(:Person)-[:KNOWS {since: 2020}]->(:Person)
```

## Basic Cypher Queries

### CREATE

Create nodes and relationships:

```cypher
CREATE (d:Document {title: "My Document"})
CREATE (p:Page {number: 1})
CREATE (d)-[:CONTAINS]->(p)
```

### MATCH

Search nodes and relationships:

```cypher
MATCH (d:Document {title: "My Document"})
RETURN d
```

### MERGE

Create only if does not exist:

```cypher
MERGE (d:Document {title: "My Document"})
ON CREATE SET d.createdAt = timestamp()
```

## Indexes in Neo4j

### Full-Text Index

For full-text search:

```cypher
CREATE FULLTEXT INDEX chunk_content FOR (c:Chunk) ON EACH [c.page_content]
```

### Vector Index

For similarity search:

```cypher
CALL db.index.vector.createNodeIndex(
    'chunk_embeddings',
    'Chunk',
    'embeddings',
    384,
    'cosine'
)
```

## Searches in Neo4j

### Full-Text Search

```cypher
CALL db.index.fulltext.queryNodes("chunk_content", "query text")
YIELD node, score
RETURN node, score
ORDER BY score DESC
LIMIT 10
```

### Vector Search

```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', 10, $query_vector)
YIELD node, score
RETURN node, score
ORDER BY score DESC
```

## References

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Neo4j Full-Text Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)
