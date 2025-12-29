# Advanced Examples

Advanced usage examples of Ungraph.

## Example 1: Ingest Multiple Documents

```python
import ungraph
from pathlib import Path

# File list
files = ["doc1.md", "doc2.txt", "doc3.docx"]

# Ingest all
for file in files:
    try:
        chunks = ungraph.ingest_document(file)
        print(f"✅ {file}: {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error with {file}: {e}")
```

## Example 2: Reconstruct Full Context

```python
import ungraph

# Search
results = ungraph.hybrid_search("topic", limit=3)

# Reconstruct full context for each result
for result in results:
    full_context = ""
    
    if result.previous_chunk_content:
        full_context += f"[Previous]\n{result.previous_chunk_content}\n\n"
    
    full_context += f"[Main]\n{result.content}\n\n"
    
    if result.next_chunk_content:
        full_context += f"[Next]\n{result.next_chunk_content}"
    
    print(full_context)
    print("=" * 80)
```

## Example 3: Create a Custom Pattern

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition
)
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService

# Create simple pattern
chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={"chunk_id": str, "content": str},
    indexes=["chunk_id"]
)

simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Only chunks",
    node_definitions=[chunk_node],
    relationship_definitions=[]
)

# Validate
service = Neo4jPatternService()
is_valid = service.validate_pattern(simple_pattern)
print(f"Valid pattern: {is_valid}")

# Generate Cypher query
cypher = service.generate_cypher(simple_pattern, "create")
print(f"Generated query:\n{cypher}")
```

## Example 4: Result Analysis

```python
import ungraph
from collections import Counter

# Search
results = ungraph.hybrid_search("machine learning", limit=20)

# Analyze results
print(f"Total results: {len(results)}")
print(f"Average score: {sum(r.score for r in results) / len(results):.3f}")
print(f"Max score: {max(r.score for r in results):.3f}")
print(f"Min score: {min(r.score for r in results):.3f}")

# Count chunks with context
with_context = sum(1 for r in results if r.previous_chunk_content or r.next_chunk_content)
print(f"Results with context: {with_context}/{len(results)}")
```

## Example 5: Compare Search Strategies

```python
import ungraph

query = "deep learning"

# Text search
text_results = ungraph.search(query, limit=5)

# Hybrid search with different weights
hybrid_1 = ungraph.hybrid_search(query, limit=5, weights=(0.7, 0.3))  # More text
hybrid_2 = ungraph.hybrid_search(query, limit=5, weights=(0.3, 0.7))  # More vector

print("Text search:")
for r in text_results[:3]:
    print(f"  Score: {r.score:.3f}")

print("\nHybrid (more text):")
for r in hybrid_1[:3]:
    print(f"  Score: {r.score:.3f}")

print("\nHybrid (more vector):")
for r in hybrid_2[:3]:
    print(f"  Score: {r.score:.3f}")
```

## Example 6: Parent-Child Retriever

Parent-Child Retriever improves result quality when full context is needed. It searches small chunks (children) and retrieves the parent chunk (full context).

```python
import ungraph
from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

# 1. Create parent-child structure (ingest document)
print("📄 Ingesting long document...")
chunks = ungraph.ingest_document(
    "technical_document.md",
    chunk_size=500,  # Small chunks for better matching
    chunk_overlap=100
)
print(f"✅ {len(chunks)} chunks created\n")

# 2. Search using Parent-Child Retriever
query = "deep neural network architecture"
print(f"🔍 Searching: '{query}'\n")

search_service = Neo4jSearchService()
results = search_service.search_with_pattern(
    query_text=query,
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=3
)

# 3. Show results with full context
print(f"📊 Found {len(results)} results:\n")
for i, result in enumerate(results, 1):
    print(f"{'='*80}")
    print(f"Result {i}")
    print(f"{'='*80}")
    print(f"📄 Page (Parent) - Score: {result.parent_score:.4f}")
    print(f"\n{result.parent_content[:400]}...")
    print(f"\n📦 Related chunks: {len(result.children)}")
    
    # Show first 3 children
    for j, child in enumerate(result.children[:3], 1):
        print(f"\n  Chunk {j}:")
        print(f"  {child['content'][:250]}...")
    
    print(f"\n{'='*80}\n")

search_service.close()
```

**When to use Parent-Child Retriever:**
- ✅ Many topics in a chunk negatively affect vector quality
- ✅ You need full section context to generate answers
- ✅ Small chunks have better vector representation but lack context

## Example 7: GraphRAG Search Patterns (Metadata Filtering)

Search with metadata filters. Useful to search only in specific documents.

```python
import ungraph

# Search only in a specific file
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md"
    },
    limit=10
)

# Search in a specific page
results = ungraph.search_with_pattern(
    "deep learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md",
        "page_number": 1
    },
    limit=5
)

# Process results
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content[:200]}...")
    print("---")
```

## Example 8: Compare Search Patterns

```python
import ungraph

query = "quantum computing"

# Normal search (no filters)
results_normal = ungraph.search(query, limit=5)
print(f"Normal search: {len(results_normal)} results")

# Search with metadata filter
results_filtered = ungraph.search_with_pattern(
    query,
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "quantum_computing.md"},
    limit=5
)
print(f"Filtered search: {len(results_filtered)} results")

# Comparison: Basic vs Parent-Child
print("\n--- Basic Retriever ---")
basic_results = ungraph.search(query, limit=3)
for r in basic_results:
    print(f"Score: {r.score:.3f} - Chunk only")

print("\n--- Parent-Child Retriever ---")
search_service = Neo4jSearchService()
parent_child_results = search_service.search_with_pattern(
    query,
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    limit=3
)
for r in parent_child_results:
    print(f"Score: {r.parent_score:.3f} - Page + {len(r.children)} child chunks")
search_service.close()
```

## References

- [Custom Patterns Guide](../guides/sp-custom-patterns.md)
- [GraphRAG Search Patterns](../api/en-search-patterns.md)
- [Lexical Graphs](../concepts/en-lexical-graphs.md)
