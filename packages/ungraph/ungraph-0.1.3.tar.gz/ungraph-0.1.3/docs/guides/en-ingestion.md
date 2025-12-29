# Document Ingestion Guide

This guide explains how to ingest documents into the knowledge graph using Ungraph.

## Basics

### Ingestion Flow

```
File → Document → Chunks → Embeddings → Neo4j Graph
```

1. **Load file**: via `DocumentLoaderService`
2. **Clean text**: optional, via `TextCleaningService`
3. **Split into chunks**: via `ChunkingService`
4. **Generate embeddings**: for each chunk via `EmbeddingService`
5. **Persist in graph**: via `ChunkRepository` to Neo4j

## Basic Usage

### Ingest a Single Document

```python
import ungraph

# Ingest with default parameters
chunks = ungraph.ingest_document("my_document.md")

print(f"✅ Ingested: {len(chunks)} chunks created")
```

### Ingestion Parameters

```python
chunks = ungraph.ingest_document(
    "document.md",
    chunk_size=1000,        # Chunk size
    chunk_overlap=200,      # Overlap between chunks
    clean_text=True,        # Clean text before processing
    database="neo4j",       # Neo4j database (optional)
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # Embedding model
)
```

## Get Chunking Recommendations

Ungraph can analyze your document and recommend the best chunking strategy:

```python
import ungraph

# Get recommendation
recommendation = ungraph.suggest_chunking_strategy("document.md")

print(f"Recommended strategy: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explanation: {recommendation.explanation}")
print(f"Quality score: {recommendation.quality_score:.2f}")

# Use the recommendation
chunks = ungraph.ingest_document(
    "document.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
```

## Supported Formats

### Markdown (.md)

```python
chunks = ungraph.ingest_document("document.md")
```

### Plain Text (.txt)

```python
chunks = ungraph.ingest_document("document.txt")
```

The system automatically detects file encoding (UTF-8, Windows-1252, Latin-1, etc.).

### Word (.docx)

```python
chunks = ungraph.ingest_document("document.docx")
```

### PDF (.pdf)

```python
chunks = ungraph.ingest_document("document.pdf")
```

The system uses `langchain-docling` (IBM Docling) to extract text and metadata from PDFs, including document structure, tables, and images.

## Complete Example

```python
import ungraph
from pathlib import Path

# 1. Configure (if you don't use environment variables)
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password"
)

# 2. Get recommendation
recommendation = ungraph.suggest_chunking_strategy("document.md")
print(f"Using: {recommendation.strategy}")

# 3. Ingest with recommended parameters
chunks = ungraph.ingest_document(
    "document.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap,
    clean_text=True
)

# 4. Verify results
print(f"✅ {len(chunks)} chunks created")
for i, chunk in enumerate(chunks[:3], 1):  # Show first 3
    print(f"\nChunk {i}:")
    print(f"  ID: {chunk.id}")
    print(f"  Content: {chunk.page_content[:100]}...")
```

## Ingest Multiple Documents

```python
import ungraph
from pathlib import Path

# Files to ingest
files = [
    "doc1.md",
    "doc2.txt",
    "doc3.docx",
    "doc4.pdf"
]

for file in files:
    try:
        chunks = ungraph.ingest_document(file)
        print(f"✅ {file}: {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error with {file}: {e}")
```

## Graph Structure Created

After ingestion, the graph has the following structure:

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                    Chunk -[:NEXT_CHUNK]-> Chunk
```

**Nodes:**
- **File**: Physical file
  - Properties: `filename`, `createdAt`
- **Page**: Page within the file
  - Properties: `filename`, `page_number`
- **Chunk**: Text fragment
  - Properties: `chunk_id`, `page_content`, `embeddings`, `embeddings_dimensions`
  - Optional: `is_unitary`, `chunk_id_consecutive`, `embedding_encoder_info`

**Relationships:**
- `File -[:CONTAINS]-> Page`: A file contains pages
- `Page -[:HAS_CHUNK]-> Chunk`: A page has chunks
- `Chunk -[:NEXT_CHUNK]-> Chunk`: Consecutive chunks are related

## Troubleshooting

### Error: UnicodeDecodeError

**Issue:** The file has a non-UTF-8 encoding.

**Solution:** The system auto-detects encodings. If the error persists, verify the file manually.

### Error: AuthError when connecting to Neo4j

**Issue:** Neo4j credentials are incorrect.

**Solution:** Check environment variables or programmatic configuration:

```python
from ungraph.core.configuration import get_settings
settings = get_settings()
print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
```

### Error: Very Large Document

**Issue:** The document is too large to process at once.

**Solution:** Consider manually splitting the document or using a smaller `chunk_size`.

## References

- [Quickstart Guide](en-quickstart.md)
- [Public API](../api/en-public-api.md)
- [Graph Patterns](../concepts/en-graph-patterns.md)
