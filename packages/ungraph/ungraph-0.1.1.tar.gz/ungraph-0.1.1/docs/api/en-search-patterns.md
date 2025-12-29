# GraphRAG Search Patterns

## Introduction

GraphRAG search patterns retrieve information from the knowledge graph using strategies optimized for different query types.

**Key idea**: These patterns leverage graph structure (especially **Lexical Graphs**) to improve retrieval. Instead of relying only on vector similarity, GraphRAG uses relationships between nodes to enrich results.

**In Ungraph**: The `FILE_PAGE_CHUNK` pattern is a Lexical Graph that supports these search patterns. See [Lexical Graphs](../concepts/en-lexical-graphs.md) for details.

**References:**
- [GraphRAG Retrieval Patterns](https://graphrag.com/reference/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Lexical Graphs in Ungraph](../concepts/en-lexical-graphs.md)

## Available Patterns

### ✅ 1. Basic Retriever (IMPLEMENTED)

**Also known as**: Naive Retriever, Basic RAG, Typical RAG

**Required graph pattern**: Lexical Graph (such as `FILE_PAGE_CHUNK`)

**Status:** ✅ **IMPLEMENTED AND AVAILABLE**

**How it works**:
1. The user query is vectorized using the same embedding model as chunks
2. Vector similarity search is executed over chunk embeddings
3. The top-`k` most similar chunks are returned directly from nodes

**When to use:**
- The requested information is in specific nodes related to topics spread across one or more chunks
- No extra context is needed beyond the matched chunk
- Keyword or simple concept searches
- High similarity between query and content

**When NOT to use:**
- When full section context is needed (use Parent-Child)
- When information is spread across many related chunks (consider Community Summary)
- When filtering by specific metadata is required (use Metadata Filtering)

**Example:**
```python
import ungraph

results = ungraph.search_with_pattern(
    "artificial intelligence",
    pattern_type="basic",
    limit=5
)
```

**Generated Cypher:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
RETURN node.page_content as content, score
ORDER BY score DESC
LIMIT $limit
```

---

### ✅ 2. Metadata Filtering (IMPLEMENTED)

Full-text search with metadata filters.

**Status:** ✅ **IMPLEMENTED AND AVAILABLE**

**When to use:**
- Search only specific documents
- Filter by date, author, document type, etc.
- Reduce search space for higher precision

**Example:**
```python
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md",
        "page_number": 1
    },
    limit=10
)
```

**Generated Cypher:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
WHERE node.filename = $filename AND node.page_number = $page_number
RETURN node.page_content as content, score
ORDER BY score DESC
LIMIT $limit
```

---

### ✅ 3. Parent-Child Retriever (IMPLEMENTED)

**Also known as**: Parent-Document Retriever

**Required graph pattern**: Lexical Graph with hierarchical structure

**Status:** ✅ **IMPLEMENTED AND AVAILABLE**

**How it works**:
This pattern evolves the basic Lexical Graph:
- **Small (child) chunks**: Contain embedded text and embeddings (better vector representation, less noise)
- **Large (parent) chunks**: Used only for context when generating answers

**Flow**:
1. Search small chunks using vector search (better matching)
2. Retrieve the related parent chunk (full context)
3. Use full context in the response

**When to use:**
- Many topics in a single chunk hurt vector quality
- Full section context is needed to answer
- Small chunks have better vectors but lack context
- Search in `Page` and retrieve all related `Chunk`s

**When NOT to use:**
- A small chunk contains enough information (use Basic Retriever)
- No parent-child hierarchy exists in your graph

**Example:**
```python
results = ungraph.search_with_pattern(
    "quantum computing",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=5
)

for result in results:
    print(f"Page: {result.parent_content}")
    print(f"Related chunks: {len(result.children)}")
```

**Generated Cypher:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as parent_node, score as parent_score

OPTIONAL MATCH (parent_node:Page)-[:HAS_CHUNK]->(child_node:Chunk)

RETURN {
    parent_content: parent_node.page_content,
    parent_score: parent_score,
    children: collect(DISTINCT {
        content: child_node.page_content,
        chunk_id: child_node.chunk_id
    })
} as result
ORDER BY parent_score DESC
LIMIT $limit
```

---

### ✅ 4. Community Summary Retriever (GDS) (IMPLEMENTED - Requires ungraph[gds])

Finds communities of related nodes and generates summaries using Graph Data Science.

**Status:** ✅ **IMPLEMENTED AND AVAILABLE** (requires `pip install ungraph[gds]` and Neo4j GDS plugin)

**See full docs**: [Advanced Search Patterns](../api/en-advanced-search-patterns.md)

**When to use:**
- Broad context needed on a topic
- Find related information across the graph
- Generate knowledge summaries

**Example:**
```python
results = ungraph.search_with_pattern(
    "deep learning",
    pattern_type="community",
    community_threshold=5,
    max_depth=2,
    limit=3
)

for result in results:
    print(f"Central chunk: {result.central_content[:100]}...")
    print(f"Community size: {result.community_size}")
    print(f"Summary: {result.community_summary[:200]}...")
```

**Generated Cypher:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as central_node, score

MATCH path = (central_node)-[*1..2]-(community_node:Chunk)
```
