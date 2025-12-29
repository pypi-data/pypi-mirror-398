# Ungraph

<div align="center">
  <img src="qnow_logo.png" alt="Qnow Logo" width="200">
</div>

<div align="center">
  <strong>A Python framework for building Knowledge Graphs from unstructured text using Neo4j and GraphRAG patterns.</strong>
</div>

---

## What is Ungraph?

Ungraph transforms unstructured documents into structured **Lexical Graphs** stored in Neo4j, enabling advanced information retrieval and semantic search through proven GraphRAG patterns.

### Problems It Solves

- **Information Overload**: Converts unstructured text into queryable knowledge graphs
- **Context Loss**: Preserves document structure and relationships through hierarchical graph patterns
- **Limited Search**: Enables semantic, hybrid, and graph-enhanced search beyond keyword matching
- **Knowledge Fragmentation**: Connects related concepts across documents through entity extraction and relationships

### Project Orientation

Ungraph is designed for:

- **RAG Applications**: Enhanced retrieval for LLM-based systems using GraphRAG patterns
- **Knowledge Management**: Building searchable knowledge bases from document collections
- **Research & Analysis**: Extracting and connecting entities, facts, and relationships from text
- **Production Systems**: Clean architecture with comprehensive testing and error handling

## Installation

### Requirements

- Python 3.12+
- Neo4j 5.x+ (running and accessible)

### Basic Installation

```bash
pip install ungraph
```

### Optional Add-ons

```bash
# Entity extraction and inference (spaCy NER)
pip install ungraph[infer]
python -m spacy download en_core_web_sm  # or es_core_news_sm for Spanish

# Advanced search patterns (Neo4j GDS)
pip install ungraph[gds]

# Graph visualization in Jupyter
pip install ungraph[ynet]

# Development tools
pip install ungraph[dev]

# All extensions
pip install ungraph[all]
```

### Neo4j Setup

**Docker (recommended):**

```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password neo4j:latest
```

**Or download:** [Neo4j Desktop](https://neo4j.com/download/) | [Community Edition](https://neo4j.com/download-center/#community)

### Configuration

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password",
    neo4j_database="neo4j"
)
```

**Or use environment variables:**

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="your_password"
export UNGRAPH_NEO4J_DATABASE="neo4j"
```

## Core Functions

Ungraph provides three essential functions: **Extract**, **Transform**, and **Infer**.

### 1. Extract

Extract text from documents and split into semantically meaningful chunks.

```python
import ungraph

# Extract and chunk a document
chunks = ungraph.ingest_document("document.pdf")
print(f"Extracted {len(chunks)} chunks")

# Get intelligent chunking recommendations
recommendation = ungraph.suggest_chunking_strategy("document.md")
print(f"Strategy: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
```

**Supported formats:** Markdown, TXT, Word, PDF
**Features:** Automatic encoding detection, intelligent chunking, text cleaning

### 2. Transform

Transform extracted chunks into a structured graph with embeddings and relationships.

```python
import ungraph

# Transform document into graph (automatic with ingest_document)
chunks = ungraph.ingest_document("document.md")

# The graph structure is automatically created:
# File → Page → Chunk (with NEXT_CHUNK relationships)
# Each chunk has vector embeddings for semantic search
```

**Graph Pattern:**

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
Chunk -[:NEXT_CHUNK]-> Chunk
```

**Features:** Vector embeddings (HuggingFace), configurable graph patterns, automatic indexing

### 3. Infer

Infer entities, relations, and facts from text using NER or LLM-based extraction.

```python
import ungraph

# Configure inference mode
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password",
    inference_mode="ner"  # or "llm" for LLM-based (experimental)
)

# Ingest with entity extraction
chunks = ungraph.ingest_document(
    "document.txt",
    extract_entities=True
)

# Search by entity
results = ungraph.search_by_entity("Apple Inc.", limit=5)
for result in results:
    print(f"Content: {result.content}")
    print(f"Entities: {[e.name for e in result.entities]}")
```

**Inference Modes:**

- **NER** (default): Fast, production-ready entity extraction with spaCy
- **LLM** (experimental): Domain-specific extraction using Ollama
- **Hybrid** (planned): Combines NER speed with LLM accuracy

## Search Capabilities

### Basic Search

```python
# Text search
results = ungraph.search("quantum computing", limit=5)

# Vector search (semantic similarity)
results = ungraph.vector_search("machine learning", limit=5)

# Hybrid search (text + vector)
results = ungraph.hybrid_search(
    "artificial intelligence",
    limit=10,
    weights=(0.4, 0.6)  # text_weight, vector_weight
)
```

### GraphRAG Patterns

```python
# Basic Retriever: Direct vector search
results = ungraph.search_with_pattern(
    "neural networks",
    pattern_type="basic",
    limit=5
)

# Parent-Child Retriever: Small chunks + full context
results = ungraph.search_with_pattern(
    "quantum entanglement",
    pattern_type="parent_child",
    limit=3
)

# Graph-Enhanced Search (requires ungraph[gds])
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2
)
```

## Architecture

Ungraph follows **Clean Architecture** principles:

```
src/
├── domain/          # Entities, Value Objects, Interfaces
├── application/     # Use cases
├── infrastructure/  # Neo4j, LangChain implementations
└── utils/           # Legacy code (being migrated)
```

**Key Features:**

- Domain-driven design
- Configurable graph patterns
- Production-ready with comprehensive testing
- Modular design with optional dependencies

## Documentation

- [Complete Documentation](docs/README.md)
- [Quick Start Guide](docs/guides/quickstart.md)
- [GraphRAG Search Patterns](docs/api/search-patterns.md)
- [Advanced Search Patterns](docs/api/advanced-search-patterns.md)
- [Graph Patterns](docs/concepts/graph-patterns.md)

## Contributing

Contributions are welcome! Please see our contributing guidelines for code style, testing requirements, and pull request process.

## License

MIT License

## Author

Alejandro Giraldo Londoño - alejandro@qnow.tech

<div align="center">
  <small>
    Developed by <a href="https://www.linkedin.com/company/qnow-tech" target="_blank">Qnow</a>
  </small>
</div>

## Citation

If you use Ungraph in your research, please cite:

```bibtex
@software{ungraph2026,
  author = {Giraldo Londoño, Alejandro},
  title = {Ungraph: Knowledge Graph Construction with GraphRAG Patterns},
  year = {2026},
  note = {In preparation},
  url = {https://github.com/Alejandro-qnow}
}

@article{giraldo2026eti,
  author = {Giraldo Londoño, Alejandro},
  title = {Extract-Transform-Inference: A Pattern for Building Traceable Knowledge Graphs in GraphRAG Systems},
  journal = {arXiv preprint},
  year = {2026},
  note = {In preparation},
}
```
