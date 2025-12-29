# Introduction to Ungraph

## What is Ungraph?

Ungraph is a Python library to convert unstructured data into knowledge graphs using Neo4j. It provides a complete pipeline to:

1. **Load documents** (Markdown, TXT, Word, PDF)
2. **Split into smart chunks** with automatic recommendations
3. **Generate embeddings** using HuggingFace models
4. **Persist into a knowledge graph** (Neo4j)
5. **Search information** using hybrid search (text + vector)

## Fundamental Concept

Ungraph assumes all unstructured data can be organized into fundamental entities using a **Lexical Graph**:

```
File → Page → Chunk
```

With relationships:
- `File -[:CONTAINS]-> Page`
- `Page -[:HAS_CHUNK]-> Chunk`
- `Chunk -[:NEXT_CHUNK]-> Chunk` (consecutive chunks)

**What is a Lexical Graph?** It's a structure that organizes text and captures linguistic relationships, facilitating semantic search. The `FILE_PAGE_CHUNK` pattern implements a Lexical Graph compatible with GraphRAG patterns like Basic Retriever and Parent-Child Retriever.

See [Lexical Graphs](./en-lexical-graphs.md) for more details.

## Key Features

### ✅ Complete Pipeline
- Load multiple formats (Markdown, TXT, Word, PDF)
- Automatic encoding detection
- Text cleaning
- Smart chunking with recommendations
- Embedding generation
- Persistence in Neo4j

### ✅ Advanced Search
- Text search (full-text search)
- Vector search (similarity search)
- Hybrid search (combination of both)
- Advanced GraphRAG patterns (Parent-Child, Community, etc.)

### ✅ Clean Architecture
- Clean Architecture for maintainability
- Clear separation of responsibilities
- Easy to test and extend
- Professional and documented code

### ✅ Pattern System
- Configurable graph patterns
- Predefined patterns ready to use
- Create custom patterns
- Automatic validation

## Use Cases

### Use Case 1: Technical Documentation
Convert technical documentation into a knowledge graph for semantic search.

### Use Case 2: Academic Research
Organize papers and academic articles into a graph for knowledge exploration.

### Use Case 3: Enterprise Knowledge Base
Build an enterprise knowledge base from internal documents.

## Installation

```bash
pip install ungraph
```

Or from source:

```bash
git clone https://github.com/your-user/ungraph.git
cd ungraph
pip install -e .
```

## Basic Usage

```python
import ungraph

# 1. Ingest a document
chunks = ungraph.ingest_document("document.md")
print(f"✅ Document split into {len(chunks)} chunks")

# 2. Search information
results = ungraph.search("sample query", limit=5)
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content[:200]}...")

# 3. Hybrid search
results = ungraph.hybrid_search(
    "artificial intelligence",
    limit=10,
    weights=(0.4, 0.6)  # More weight to vector search
)
```

## Requirements

- Python 3.12+
- Neo4j 5.x
- Dependencies listed in `pyproject.toml`

## References

- [Main README](../../README.md)
- [Quickstart Guide](../guides/en-quickstart.md)
- [System Architecture](en-architecture.md)
