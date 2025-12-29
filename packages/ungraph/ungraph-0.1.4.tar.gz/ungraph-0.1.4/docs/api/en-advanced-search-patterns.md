# GraphRAG Advanced Search Patterns

## Introduction

Advanced search patterns require optional modules and provide more sophisticated capabilities to retrieve information from the graph.

**Installation**:
```bash
# For advanced patterns with Graph Data Science
pip install ungraph[gds]

# For graph visualization
pip install ungraph[ynet]

# For all extensions
pip install ungraph[all]
```

## Available Advanced Patterns

### 1. Graph-Enhanced Vector Search ⭐ RECOMMENDED

**Requirements**: `ungraph[gds]` and extracted entities in the graph

**How it works**:
1. Finds similar chunks using embeddings (vector search)
2. Extracts entities mentioned in those chunks
3. Traverses the graph from those entities to find related chunks
4. Returns enriched context with related information

**Advantages**:
- Finds related information not present in the original chunk
- Connects concepts through entities
- Provides more complete context for the LLM

**Example**:
```python
import ungraph

# Graph-Enhanced search
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2  # Depth of relationships to explore
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.content[:200]}...")
    if result.next_chunk_content:
        print(f"Related context: {result.next_chunk_content[:200]}...")
```

**Generated Cypher Query**:
```cypher
// 1. Initial vector search
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $query_vector)
YIELD node as initial_chunk, score as initial_score

// 2. Find mentioned entities
OPTIONAL MATCH (initial_chunk)-[:MENTIONS]->(entity:Entity)

// 3. Find other chunks related through entities
OPTIONAL MATCH path = (entity)<-[:MENTIONS]-(related_chunk:Chunk)
WHERE related_chunk <> initial_chunk

// 4. Return enriched context
RETURN {
    central_chunk: {...},
    related_chunks: [...],
    neighbor_chunks: [...]
} as result
```

---

### 2. Local Retriever

**Requirements**: `ungraph[gds]` (optional, works without GDS but better with it)

**How it works**:
1. Finds the central chunk using full-text search
2. Finds local community (chunks related through graph relationships)
3. Groups related chunks and generates context

**Advantages**:
- Optimized for small, focused communities
- Faster than Community Summary
- Useful for exploring specific knowledge

**Example**:
```python
import ungraph

results = ungraph.search_with_pattern(
    "neural networks",
    pattern_type="local",
    limit=5,
    community_threshold=3,  # Minimum community size
    max_depth=1  # Relationship depth
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Central content: {result.content[:200]}...")
    if result.next_chunk_content:
        print(f"Community summary: {result.next_chunk_content[:200]}...")
```

---

### 3. Community Summary Retriever (GDS)

**Requirements**: `ungraph[gds]` and Neo4j GDS plugin installed

**How it works**:
1. Uses GDS community detection algorithms (Louvain, Leiden)
2. Detects communities of related chunks
3. Generates summaries of each community
4. Searches in summaries instead of individual chunks

**Advantages**:
- Finds related topics even across different chunks
- Summaries capture the full context of a topic
- Reduces noise by searching in summaries

**Pre-requisites**:
Before using this pattern, you must detect communities:

```python
from infrastructure.services.gds_service import GDSService

gds_service = GDSService()
stats = gds_service.detect_communities(
    graph_name="chunk-graph",
    algorithm="louvain",
    write_property="community_id"
)
print(f"Detected {stats['community_count']} communities")
```

**Example**:
```python
import ungraph

# First detect communities (once)
from infrastructure.services.gds_service import GDSService
gds_service = GDSService()
gds_service.detect_communities()

# Then search using Community Summary
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="community_summary",
    limit=3,
    min_community_size=5
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.content[:200]}...")
    if result.next_chunk_content:
        print(f"Community summary: {result.next_chunk_content[:200]}...")
```

---

## Pattern Comparison

| Pattern | Requirements | Speed | Accuracy | Context | Use |
|--------|-----------|-----------|-----------|----------|-----|
| Basic | None | ⚡⚡⚡ | ⭐⭐ | ⭐ | Simple searches |
| Metadata Filtering | None | ⚡⚡⚡ | ⭐⭐⭐ | ⭐ | Filter by properties |
| Parent-Child | None | ⚡⚡ | ⭐⭐⭐ | ⭐⭐ | Hierarchical context |
| Graph-Enhanced | ungraph[gds] | ⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Advanced searches |
| Local | ungraph[gds] | ⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | Small communities |
| Community Summary | ungraph[gds] + GDS | ⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Related topics |

---

## Best Practices

1. **Start simple**: Use `basic` or `metadata_filtering` first
2. **Adjust as needed**: If you need more context, use `parent_child`
3. **For advanced searches**: Use `graph_enhanced` when you have extracted entities
4. **For related topics**: Use `community_summary` when you need to find distributed information
5. **Performance**: Advanced patterns are slower but provide better context

---

## Index Requirements

**Basic indices** (always required):
- `chunk_content`: Full-text index
- `chunk_embeddings`: Vector index

**Additional indices** (for advanced patterns):
- `Entity` nodes with `MENTIONS` relationships (for Graph-Enhanced)
- `community_id` property on chunks (for Community Summary, requires GDS)
