# Custom Graph Patterns Guide

This guide explains how to create and use custom graph patterns in Ungraph.

## What Are Patterns?

Patterns define the structure of the knowledge graph. The default pattern is `FILE_PAGE_CHUNK`, but you can create custom patterns for different needs.

## Create a Simple Pattern

### Example: Chunks Only

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition
)

# Define Chunk node
chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={
        "chunk_id": str,
        "content": str
    },
    indexes=["chunk_id"]
)

# Create pattern
simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Chunks only, no File-Page structure",
    node_definitions=[chunk_node],
    relationship_definitions=[]
)
```

## Create a Pattern with Relationships

### Example: Entities and Chunks

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition
)

# Entity node
entity_node = NodeDefinition(
    label="Entity",
    required_properties={
        "name": str,
        "type": str
    },
    optional_properties={
        "description": str
    },
    indexes=["name", "type"]
)

# Chunk node
chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={
        "chunk_id": str,
        "content": str
    },
    indexes=["chunk_id"]
)

# Relationship: Chunk mentions Entity
mentions_rel = RelationshipDefinition(
    from_node="Chunk",
    to_node="Entity",
    relationship_type="MENTIONS",
    properties={"count": int},  # Relationship property
    direction="OUTGOING"
)

# Create pattern
lexical_pattern = GraphPattern(
    name="LEXICAL_GRAPH",
    description="Lexical graph with entities and chunks",
    node_definitions=[entity_node, chunk_node],
    relationship_definitions=[mentions_rel]
)
```

## Validate a Pattern

Before using a pattern, validate it:

```python
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService

service = Neo4jPatternService()
is_valid = service.validate_pattern(my_pattern)

if is_valid:
    print("✅ Valid pattern")
else:
    print("❌ Invalid pattern")
```

## Generate Cypher Query

You can inspect the Cypher query that would be generated for your pattern:

```python
service = Neo4jPatternService()
cypher_query = service.generate_cypher(my_pattern, "create")

print("Generated Cypher query:")
print(cypher_query)
```

## Use a Custom Pattern

**Note:** Integration with `ingest_document()` is under development (Phase 2). For now, use the pattern directly via `PatternService`:

```python
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService

service = Neo4jPatternService()

# Data for the pattern
data = {
    "chunk_id": "chunk_1",
    "content": "Chunk content"
}

# Apply pattern (requires configured Neo4j)
# service.apply_pattern(simple_pattern, data)
```

## Validation Rules

### Node Labels

- Must start with uppercase
- Only letters, numbers, and underscores
- Valid examples: `File`, `Page`, `Chunk`, `Entity`
- Invalid examples: `file`, `File-Name`, `file_name`

### Relationship Types

- Must start uppercase
- Only uppercase letters, numbers, and underscores
- Valid examples: `CONTAINS`, `HAS_CHUNK`, `NEXT_CHUNK`
- Invalid examples: `contains`, `has-chunk`

### Properties

- Names must be valid Python identifiers
- Types must be Python types (`str`, `int`, `list`, etc.)

## Full Examples

### Pattern: Document → Section → Paragraph

```python
document_node = NodeDefinition(
    label="Document",
    required_properties={"doc_id": str, "title": str},
    indexes=["doc_id"]
)

section_node = NodeDefinition(
    label="Section",
    required_properties={"section_id": str, "title": str},
    indexes=["section_id"]
)

paragraph_node = NodeDefinition(
    label="Paragraph",
    required_properties={"para_id": str, "content": str},
    indexes=["para_id"]
)

# Relationships
has_section = RelationshipDefinition(
    from_node="Document",
    to_node="Section",
    relationship_type="HAS_SECTION"
)

has_paragraph = RelationshipDefinition(
    from_node="Section",
    to_node="Paragraph",
    relationship_type="HAS_PARAGRAPH"
)

document_pattern = GraphPattern(
    name="DOCUMENT_SECTION_PARAGRAPH",
    description="Document contains sections, sections contain paragraphs",
    node_definitions=[document_node, section_node, paragraph_node],
    relationship_definitions=[has_section, has_paragraph]
)
```

## References

- [Graph Patterns Documentation](../concepts/en-graph-patterns.md)
- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
