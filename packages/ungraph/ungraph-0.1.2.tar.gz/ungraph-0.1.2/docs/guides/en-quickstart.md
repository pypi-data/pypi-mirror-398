# Quickstart Guide

This guide helps you get started with Ungraph in minutes.

## Installation

```bash
pip install ungraph
```

## Initial Configuration

### Option 1: Environment Variables

Create a `.env` file at the project root:

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=your_password
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Option 2: Programmatic Configuration

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

## First Example: Ingest a Document

```python
import ungraph
from pathlib import Path

# Ingest a document
chunks = ungraph.ingest_document(
    "my_document.md",
    chunk_size=1000,
    chunk_overlap=200
)

print(f"✅ Document ingested successfully!")
print(f"   Total chunks: {len(chunks)}")
```

## Second Example: Search

```python
# Simple text search
results = ungraph.search("quantum computing", limit=5)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content[:200]}...")
    print("---")
```

## Third Example: Hybrid Search

```python
# Hybrid search (text + vector)
results = ungraph.hybrid_search(
    "artificial intelligence",
    limit=10,
    weights=(0.3, 0.7)  # 30% text, 70% vector
)

for result in results:
    print(f"Combined score: {result.score:.3f}")
    print(f"Content: {result.content}")
    
    # Additional context
    if result.previous_chunk_content:
        print(f"Previous context: {result.previous_chunk_content[:100]}...")
    if result.next_chunk_content:
        print(f"Next context: {result.next_chunk_content[:100]}...")
    print("=" * 80)
```

## Fourth Example: Chunking Recommendations

```python
# Get recommended chunking strategy
recommendation = ungraph.suggest_chunking_strategy("my_document.md")

print(f"Recommended strategy: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explanation: {recommendation.explanation}")
print(f"Quality score: {recommendation.quality_score:.2f}")
```

## End-to-End Example

```python
import ungraph
from pathlib import Path

# 1. Configure (if not using environment variables)
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password"
)

# 2. Get chunking recommendation
recommendation = ungraph.suggest_chunking_strategy("document.md")
print(f"Using strategy: {recommendation.strategy}")

# 3. Ingest document with recommended parameters
chunks = ungraph.ingest_document(
    "document.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
print(f"✅ {len(chunks)} chunks created")

# 4. Search
results = ungraph.hybrid_search(
    "topic of interest",
    limit=5
)

# 5. Process results
for result in results:
    full_context = ""
    if result.previous_chunk_content:
        full_context += f"[Previous] {result.previous_chunk_content}\n\n"
    full_context += f"[Current] {result.content}\n\n"
    if result.next_chunk_content:
        full_context += f"[Next] {result.next_chunk_content}"
    
    print(full_context)
    print("=" * 80)
```

## Next Steps

- [Ingestion Guide](en-ingestion.md) - Learn more about ingestion
- [Search Guide](../guides/search.md) - Explore advanced search patterns
- [Custom Patterns](en-custom-patterns.md) - Create your own patterns
- [Advanced Examples](../examples/advanced-examples.md) - Complex use-cases

## Troubleshooting

### Error: AuthError connecting to Neo4j

**Solution:** Ensure:
1. Neo4j is running
2. Credentials are correct
3. URI is reachable (port 7687 by default)

```python
# Verify configuration
from ungraph.core.configuration import get_settings
settings = get_settings()
print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
```

### Error: UnicodeDecodeError when loading file

**Solution:** The system auto-detects encoding, but if it persists:

```python
# The system attempts multiple encodings automatically:
# utf-8, windows-1252, latin-1, iso-8859-1, cp1252
# If it fails, verify the file manually
```

## References

- [Main README](../../README.md)
- [API Docs](../api/en-public-api.md)
- [Configuration](../api/en-configuration.md)
