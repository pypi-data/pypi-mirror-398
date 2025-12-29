# Basic Examples

Simple usage examples of Ungraph.

## Example 1: Ingest a Document

```python
import ungraph

# Ingest document
chunks = ungraph.ingest_document("my_document.md")

print(f"✅ Document ingested: {len(chunks)} chunks created")
```

## Example 2: Search Information

```python
import ungraph

# Search
results = ungraph.search("topic of interest", limit=5)

# Show results
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content[:200]}...")
    print("---")
```

## Example 3: Hybrid Search

```python
import ungraph

# Hybrid search
results = ungraph.hybrid_search(
    "artificial intelligence",
    limit=10,
    weights=(0.3, 0.7)
)

# Process results
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content}")
    print("=" * 80)
```

## Example 4: Get Chunking Recommendation

```python
import ungraph

# Get recommendation
recommendation = ungraph.suggest_chunking_strategy("document.md")

print(f"Strategy: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explanation: {recommendation.explanation}")

# Use recommendation
chunks = ungraph.ingest_document(
    "document.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
```

## Example 5: End-to-End Pipeline

```python
import ungraph

# 1. Configure
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password"
)

# 2. Get recommendation
recommendation = ungraph.suggest_chunking_strategy("document.md")

# 3. Ingest
chunks = ungraph.ingest_document(
    "document.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)

# 4. Search
results = ungraph.hybrid_search("topic", limit=5)

# 5. Show results
for result in results:
    print(result.content)
```

## Example 6: Basic Retriever with Lexical Graph

The Basic Retriever is the simplest GraphRAG pattern. It requires a Lexical Graph (like `FILE_PAGE_CHUNK`) and works by searching similarity directly on chunks.

```python
import ungraph

# 1. Create Lexical Graph (ingest document)
print("📄 Ingesting document...")
chunks = ungraph.ingest_document(
    "technical_document.md",
    chunk_size=1000,
    chunk_overlap=200
)
print(f"✅ {len(chunks)} chunks created in the Lexical Graph\n")

# 2. Search using Basic Retriever
query = "artificial intelligence and its applications"
print(f"🔍 Searching: '{query}'\n")

results = ungraph.search(query, limit=5)

# 3. Show results
print(f"📊 Found {len(results)} results:\n")
for i, result in enumerate(results, 1):
    print(f"{'='*80}")
    print(f"Result {i}")
    print(f"{'='*80}")
    print(f"Similarity score: {result.score:.4f}")
    print(f"Chunk ID: {result.chunk_id}")
    print(f"\nContent:")
    print(f"{result.content[:500]}...")
    print()
```

**When to use Basic Retriever:**
- ✅ Information is in specific, well-defined chunks
- ✅ No additional context is needed beyond the found chunk
- ✅ You want the fastest and simplest search

**When NOT to use Basic Retriever:**
- ❌ You need full section context → Use **Parent-Child Retriever**
- ❌ You need to filter by metadata → Use **Metadata Filtering**

## References

- [Quickstart Guide](../guides/en-quickstart.md)
- [Ingestion Guide](../guides/en-ingestion.md)
- [Search Guide](../guides/search.md)
- [GraphRAG Search Patterns](../api/en-search-patterns.md)
