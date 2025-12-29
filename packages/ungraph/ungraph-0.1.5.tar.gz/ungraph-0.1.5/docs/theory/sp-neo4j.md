# Neo4j y Cypher

## Introducción a Neo4j

Neo4j es una base de datos de grafos que almacena datos como nodos y relaciones, permitiendo consultas eficientes sobre relaciones complejas.

## Conceptos Básicos

### Nodos (Nodes)

Representan entidades en el grafo:

```cypher
(:Person {name: "Alice"})
(:Document {title: "Introduction"})
```

### Relaciones (Relationships)

Conectan nodos:

```cypher
(:Person)-[:KNOWS]->(:Person)
(:Document)-[:CONTAINS]->(:Page)
```

### Propiedades

Tanto nodos como relaciones pueden tener propiedades:

```cypher
(:Person {name: "Alice", age: 30})
(:Person)-[:KNOWS {since: 2020}]->(:Person)
```

## Queries Cypher Básicos

### CREATE

Crear nodos y relaciones:

```cypher
CREATE (d:Document {title: "My Document"})
CREATE (p:Page {number: 1})
CREATE (d)-[:CONTAINS]->(p)
```

### MATCH

Buscar nodos y relaciones:

```cypher
MATCH (d:Document {title: "My Document"})
RETURN d
```

### MERGE

Crear solo si no existe:

```cypher
MERGE (d:Document {title: "My Document"})
ON CREATE SET d.createdAt = timestamp()
```

## Índices en Neo4j

### Índice Full-Text

Para búsqueda de texto completo:

```cypher
CREATE FULLTEXT INDEX chunk_content FOR (c:Chunk) ON EACH [c.page_content]
```

### Índice Vectorial

Para búsqueda por similitud:

```cypher
CALL db.index.vector.createNodeIndex(
    'chunk_embeddings',
    'Chunk',
    'embeddings',
    384,
    'cosine'
)
```

## Búsquedas en Neo4j

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

## Referencias

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Neo4j Full-Text Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)
