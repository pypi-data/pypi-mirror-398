# Graph Patterns

## Introduction

Graph patterns allow you to define knowledge structures declaratively and reuse them. Instead of hardcoding every structure, you can define patterns that describe how nodes and relationships should be organized in the graph.

## Lexical Graphs vs Knowledge Graphs

Before diving into patterns, it’s important to understand two fundamental concepts:

- **Lexical Graph**: Structure that organizes text and captures linguistic relationships. It focuses on language structure and facilitates semantic search. The `FILE_PAGE_CHUNK` pattern is an example of a Lexical Graph.

- **Knowledge Graph**: Structure that represents factual knowledge and relationships between domain entities. It focuses on verifiable facts and structured schemas.

**In Ungraph**: Most implemented patterns are **Lexical Graphs** because they organize unstructured text for search and retrieval. See [Lexical Graphs](./en-lexical-graphs.md) for more details.

## Basic Concepts

### NodeDefinition

Defines a type of node in the pattern:

```python
from ungraph.domain.value_objects.graph_pattern import NodeDefinition

file_node = NodeDefinition(
    label="File",
    required_properties={"filename": str},
    optional_properties={"createdAt": int},
    indexes=["filename"]
)
```

**Characteristics:**
- `label`: Node label in Neo4j (must start with uppercase)
- `required_properties`: Required properties {name: type}
- `optional_properties`: Optional properties {name: type}
- `indexes`: List of properties to index for faster searches

### RelationshipDefinition

Defines a relationship between nodes:

```python
from ungraph.domain.value_objects.graph_pattern import RelationshipDefinition

contains_rel = RelationshipDefinition(
    from_node="File",
    to_node="Page",
    relationship_type="CONTAINS",
    direction="OUTGOING"
)
```

**Characteristics:**
- `from_node`: Source node label
- `to_node`: Target node label
- `relationship_type`: Relationship type (must start with uppercase)
- `direction`: "OUTGOING" or "INCOMING"
- `properties`: Optional relationship properties

### GraphPattern

A complete pattern combining nodes and relationships:

```python
from ungraph.domain.value_objects.graph_pattern import GraphPattern

pattern = GraphPattern(
    name="FILE_PAGE_CHUNK",
    description="File contains Pages, Pages contain Chunks",
    node_definitions=[file_node, page_node, chunk_node],
    relationship_definitions=[contains_rel, has_chunk_rel]
)
```

## Predefined Pattern: FILE_PAGE_CHUNK

This is the default pattern used in Ungraph. It is a **Lexical Graph** that organizes unstructured text for semantic search.

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                    Chunk -[:NEXT_CHUNK]-> Chunk
```

### Why is it a Lexical Graph?

This pattern is a Lexical Graph because:
- **Organizes text structurally**: Splits documents into related chunks
- **Captures linguistic relationships**: Chunks are connected by relationships reflecting the text structure
- **Facilitates semantic search**: Embeddings in each chunk enable semantic similarity search
- **Supports GraphRAG patterns**: Compatible with Basic Retriever and Parent-Child Retriever

### Structure

- **File**: Represents a physical file
  - Properties: `filename`, `createdAt` (optional)
- **Page**: Represents a page within the file
  - Properties: `filename`, `page_number`
- **Chunk**: Represents a text fragment with embeddings
  - Properties: `chunk_id`, `page_content`, `embeddings`, `embeddings_dimensions`
  - Optional: `is_unitary`, `chunk_id_consecutive`, `embedding_encoder_info`

### Relationships

- `File -[:CONTAINS]-> Page`: A file contains pages
- `Page -[:HAS_CHUNK]-> Chunk`: A page has chunks
- `Chunk -[:NEXT_CHUNK]-> Chunk`: Consecutive chunks are related (enables sequential navigation)

### Use in GraphRAG

This pattern is compatible with:
- ✅ **Basic Retriever**: Direct vector search on chunks
- ✅ **Parent-Child Retriever**: Can evolve to parent-child structure
- ✅ **Metadata Filtering**: Filter by File/Page properties

See [Lexical Graphs](./en-lexical-graphs.md) for more on how this pattern works in GraphRAG.

## Create Custom Patterns

### Example: Simple Pattern (Chunks Only)

```python
from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition
)

simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Only chunks, no File-Page structure",
    node_definitions=[
        NodeDefinition(
            label="Chunk",
            required_properties={
                "chunk_id": str,
                "content": str
            },
            indexes=["chunk_id"]
        )
    ],
    relationship_definitions=[]
)
```

### Example: Pattern with Custom Relationships

```python
entity_node = NodeDefinition(
    label="Entity",
    required_properties={"name": str, "type": str},
    indexes=["name"]
)

chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={"chunk_id": str, "content": str},
    indexes=["chunk_id"]
)

# Relationship: Chunk mentions Entity
mentions_rel = RelationshipDefinition(
    from_node="Chunk",
    to_node="Entity",
    relationship_type="MENTIONS",
    properties={"count": int},  # Property on the relationship
    direction="OUTGOING"
)

lexical_pattern = GraphPattern(
    name="LEXICAL_GRAPH",
    description="Lexical graph with entities and chunks",
    node_definitions=[entity_node, chunk_node],
    relationship_definitions=[mentions_rel]
)
```

## Validations

Patterns are validated automatically:

1. **Labels and Relationship Types**: Must start with uppercase and contain only letters, numbers, and underscores
2. **Properties**: Names must be valid Python identifiers
3. **Relationships**: Must reference nodes that exist in the pattern
4. **Indexes**: Can only index properties that exist

## Pattern Usage

### In Ingestion

```python
import ungraph
from ungraph.domain.value_objects.predefined_patterns import FILE_PAGE_CHUNK_PATTERN

# Use predefined pattern
chunks = ungraph.ingest_document(
    "document.md",
    pattern=FILE_PAGE_CHUNK_PATTERN
)

# Or use a custom pattern
chunks = ungraph.ingest_document(
    "document.md",
    pattern=simple_pattern
)
```

### Validate a Pattern

```python
from ungraph.infrastructure.services.neo4j_pattern_service import Neo4jPatternService

service = Neo4jPatternService()
is_valid = service.validate_pattern(my_pattern)

if is_valid:
    print("Valid pattern")
else:
    print("Invalid pattern")
```

## References

- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [Neo4j Cypher Manual - Patterns](https://neo4j.com/docs/cypher-manual/current/patterns/)
- [Clean Architecture - Value Objects](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
