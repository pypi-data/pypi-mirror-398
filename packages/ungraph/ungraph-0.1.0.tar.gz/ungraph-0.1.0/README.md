# Ungraph

A Python framework for building Knowledge Graphs from unstructured text using Neo4j and GraphRAG patterns.

## Purpose

Ungraph is a production-ready Python library that transforms unstructured documents into structured **Lexical Graphs** stored in Neo4j. It implements proven **GraphRAG patterns** to enable advanced information retrieval and semantic search capabilities.

### What Ungraph Does

Ungraph provides a complete pipeline for knowledge graph construction and retrieval:

1. **Document Loading**: Ingests multiple document formats (Markdown, TXT, Word, PDF) with automatic encoding detection and text extraction
2. **Intelligent Chunking**: Splits documents into semantically meaningful chunks with automatic strategy recommendations based on document characteristics
3. **Vector Embeddings**: Generates high-quality embeddings using HuggingFace models for semantic similarity search
4. **Graph Persistence**: Stores documents in Neo4j as Lexical Graphs with configurable patterns (File → Page → Chunk hierarchy)
5. **Advanced Search**: Enables hybrid search (text + vector) and implements GraphRAG patterns including Basic Retriever, Parent-Child Retriever, and Metadata Filtering
6. **Entity Extraction**: Extracts entities, relations, and facts from text using spaCy NER or LLM-based inference (experimental)

### Key Differentiators

- **Clean Architecture**: Domain-driven design with clear separation of concerns, making the codebase maintainable and extensible
- **Configurable Graph Patterns**: Define custom graph structures beyond the default FILE_PAGE_CHUNK pattern to match your domain
- **GraphRAG Native**: Built from the ground up to support GraphRAG retrieval patterns for enhanced RAG applications
- **Production Ready**: Includes comprehensive testing, error handling, and configuration management
- **Modular Design**: Optional dependencies allow you to install only what you need (inference, GDS, visualization, etc.)

### Core Concept: Lexical Graphs

Ungraph implements **Lexical Graphs** (as defined in GraphRAG methodology) that organize text into chunks with structural relationships. The default `FILE_PAGE_CHUNK` pattern creates a three-level hierarchy:

```
File (document) → Page (sections) → Chunk (text fragments)
```

With relationships:
- `File -[:CONTAINS]-> Page` - Documents contain pages/sections
- `Page -[:HAS_CHUNK]-> Chunk` - Pages are divided into chunks
- `Chunk -[:NEXT_CHUNK]-> Chunk` - Sequential chunks are linked
- `Chunk -[:MENTIONS]-> Entity` - Chunks reference extracted entities (with inference enabled)

This structure enables:
- **Semantic Search**: Vector similarity search within chunks
- **Contextual Retrieval**: Accessing surrounding chunks for better context
- **Hierarchical Queries**: Traversing from chunks to pages to documents
- **Entity-Based Exploration**: Following entity mentions across documents

## Installation

### Requirements

- **Python**: 3.12 or higher
- **Neo4j**: 5.x or higher (must be running and accessible)
- **Basic Dependencies**: Automatically installed with pip

### Basic Installation

```bash
pip install ungraph
```

### Optional Modules

Install optional modules for advanced functionality:

```bash
# Inference - Entity extraction and fact inference using spaCy NER
pip install ungraph[infer]
# Then download the language model:
python -m spacy download en_core_web_sm  # For English
# or
python -m spacy download es_core_news_sm  # For Spanish

# Graph Data Science - Advanced search patterns with Neo4j GDS
pip install ungraph[gds]

# Visualization - Graph visualization in Jupyter notebooks
pip install ungraph[ynet]

# Development - Testing and development tools
pip install ungraph[dev]

# Experiments - Evaluation and experimentation framework
pip install ungraph[experiments]

# All Extensions - Install everything
pip install ungraph[all]
```

### Neo4j Setup

If you don't have Neo4j installed:

1. **Docker** (recommended):
   ```bash
   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

2. **Direct Download**: [Neo4j Desktop](https://neo4j.com/download/) or [Neo4j Community Edition](https://neo4j.com/download-center/#community)

### Installing from Source

```bash
git clone https://github.com/your-user/ungraph.git
cd ungraph
pip install -e .
```

### Initial Configuration

Before using Ungraph, configure the Neo4j connection:

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password",
    neo4j_database="neo4j"
)
```

Or using environment variables:

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="your_password"
export UNGRAPH_NEO4J_DATABASE="neo4j"
```

## Quick Start

**Note**: Ensure Neo4j is running and configured before executing these examples.

### Ingesting a Document

```python
import ungraph

# Configure connection (if not using environment variables)
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password"
)

# Ingest a document into the graph
chunks = ungraph.ingest_document("my_document.md")

print(f"Document split into {len(chunks)} chunks")
```

### Getting Chunking Recommendations

```python
import ungraph

# Get intelligent chunking strategy recommendation
recommendation = ungraph.suggest_chunking_strategy("document.md")

print(f"Recommended strategy: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explanation: {recommendation.explanation}")
```

### Searching the Graph

```python
import ungraph

# Simple text search
results = ungraph.search("quantum computing", limit=5)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content[:200]}...")
```

### Hybrid Search

```python
import ungraph

# Hybrid search (text + vector)
results = ungraph.hybrid_search(
    "artificial intelligence",
    limit=10,
    weights=(0.4, 0.6)  # More weight to vector search
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content}")
    if result.previous_chunk_content:
        print(f"Previous context: {result.previous_chunk_content}")
    if result.next_chunk_content:
        print(f"Next context: {result.next_chunk_content}")
```

### Advanced Search Patterns (requires ungraph[gds])

```python
import ungraph

# Graph-Enhanced Vector Search: Find related context through entities
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2
)

# Local Retriever: Search within small communities
results = ungraph.search_with_pattern(
    "neural networks",
    pattern_type="local",
    limit=5,
    community_threshold=3
)
```

See [Advanced Search Patterns](docs/api/advanced-search-patterns.md) for more details.

## Configuration

### Environment Variables

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="your_password"
export UNGRAPH_NEO4J_DATABASE="neo4j"
export UNGRAPH_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
export UNGRAPH_INFERENCE_MODE="ner"  # Options: ner, llm, hybrid
export UNGRAPH_OLLAMA_MODEL="llama3:8b"  # For LLM inference mode
```

Or create a `.env` file:

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=your_password
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
UNGRAPH_INFERENCE_MODE=ner
UNGRAPH_OLLAMA_MODEL=llama3:8b
```

### Programmatic Configuration

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    inference_mode="ner"  # or "llm" for LLM-based inference (experimental)
)
```
Fundamental Concepts
- [Introduction](docs/concepts/introduction.md) - Overview and purpose
- [Graph Patterns](docs/concepts/graph-patterns.md) - Configurable pattern system

### Usage Guides
- [Quick Start Guide](docs/guides/quickstart.md) - First steps
- [GraphRAG Search Patterns](docs/api/search-patterns.md) - Complete reference (basic patterns)
- [Advanced Search Patterns](docs/api/advanced-search-patterns.md) - Advanced patterns (require optional modules)
- [Lexical Graphs](docs/concepts/lexical-graphs.md) - Fundamental concepts

### Practical Examples
- [Basic Retriever with Lexical Graph](docs/examples/basic-retriever-lexical.md) - Complete example
- [Parent-Child Retriever](docs/examples/parent-child-retriever.md) - Advanced pattern

### Notebooks
- [Notebook: Using Ungraph Library](src/notebooks/1.%20Using%20Ungraph%20Library.ipynb) - Complete example
- [Notebook: Testing Graph Patterns](src/notebooks/2.%20Testing%20Graph%20Patterns.ipynb) - Systematic testing

## Architecture
### Ejemplos
- [Notebook: Uso de la Librería](src/notebooks/1.%20Using%20Ungraph%20Library.ipynb) - Ejemplo completo
- [Notebook: Testing Graph Patterns](src/notebooks/2.%20Testing%20Graph%20Patterns.ipynb) - Pruebas sistemáticas

## 🏗️ Arquitectura

The project follows **Clean Architecture** with the following layers:

```
src/
├── domain/          # Entities, Value Objects, Interfaces
│   ├── entities/   # Chunk, Document, File, Page
│   ├── value_objects/  # GraphPattern, Embedding, DocumentType
│   └── services/    # Interfaces (ChunkingService, SearchService, etc.)
├── application/     # Use cases
│   └── use_cases/   # IngestDocumentUseCase, etc.
├── infrastructure/  # Implementations (Neo4j, LangChain)
│   ├── repositories/  # Neo4jChunkRepository
│   └── services/    # Concrete implementations
└── utils/           # Legacy code (being migrated)
```

**References:**
- [Clean Architecture Principles](docs/theory/clean-architecture.md)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

## Testing

```bash
# Unit tests (no Neo4j required)
pytest tests/test_domain_entities.py -v
pytest tests/test_graph_patterns.py -v
pytest tests/test_pattern_service.py -v
pytest tests/test_llm_inference_service.py -v

# Integration tests (require Neo4j)
pytest tests/test_use_case_integration.py -v -m integration
pytest tests/test_llm_inference_integration.py -v -m integration
```

## MIngestion Pipeline
- Support for multiple formats (Markdown, TXT, Word, PDF)
- Automatic encoding detection
- Configurable text cleaning
- Intelligent chunking with automatic recommendations
- HuggingFace embeddings (configurable)
- Neo4j persistence with File → Page → Chunk structure
- Entity extraction with spaCy NER or LLM-based inference

### Pattern System
- Configurable graph patterns
- Predefined FILE_PAGE_CHUNK pattern
- Custom pattern creation
- Automatic pattern validation
- Dynamic Cypher query generation

### Advanced Search
- Text search (full-text search)
- Vector search (similarity search)
- Hybrid search (combination of both)
- Basic GraphRAG patterns (Basic Retriever, Parent-Child, Metadata Filtering)
- Advanced GraphRAG patterns (require optional modules):
  - Graph-Enhanced Vector Search (ungraph[gds])
  - Local Retriever (ungraph[gds])
  - Community Summary Retriever (ungraph[gds])

### Inference Capabilities (Experimental in v0.1.0)
- spaCy NER-based entity extraction (production-ready)
- LLM-based entity extraction using Ollama (experimental)
- Relation extraction between entities
- Fact inference from text
- Multiple inference modes: ner, llm, hybrid

### Architecture and Quality
- Clean Architecture for maintainability
- Domain-Driven Design
- Comprehensive testing with real data
- Complete documentation

## System Flow

```
1. Load file          → DocumentLoaderService
2. Clean text         → TextCleaningService
3. Split into chunks  → ChunkingService (with recommendations)
4. Generate embeddings → EmbeddingService
5. Configure indexes  → IndexService
### Example 1: Basic Document Ingestion

```python
import ungraph
from pathlib import Path

# Configure connection
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password"
)

# Ingest a document
chunks = ungraph.ingest_document("research_paper.pdf")
print(f"Document split into {len(chunks)} chunks")
```

**Expected Result:**
```
Document split into 47 chunks
```

The document is loaded, cleaned, split into chunks, embeddings are generated, and everything is persisted to Neo4j with the FILE_PAGE_CHUNK pattern:
- 1 File node created
- N Page nodes created (based on document structure)
- 47 Chunk nodes created with embeddings
- CONTAINS and HAS_CHUNK relationships established
- NEXT_CHUNK relationships linking consecutive chunks

### Example 2: Intelligent Chunking with Recommendations

```python
import ungraph

# Get chunking strategy recommendation
recommendation = ungraph.suggest_chunking_strategy("technical_documentation.md")

print(f"Recommended strategy: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Reasoning: {recommendation.explanation}")

# Apply recommended settings
chunks = ungraph.i

Ungraph implements **Lexical Graphs** that organize text and capture linguistic relationships. The default `FILE_PAGE_CHUNK` pattern is a Lexical Graph:

```
File → Page → Chunk
```

With relationships:
- `File -[:CONTAINS]-> Page`
- `Page -[:HAS_CHUNK]-> Chunk`
- `Chunk -[:NEXT_CHUNK]-> Chunk` (consecutive chunks)
- `Chunk -[:MENTIONS]-> Entity` (with inference enabled)

**Why Lexical Graphs?**
- Structurally organizes text for semantic search
- Compatible with GraphRAG patterns (Basic Retriever, Parent-Child Retriever)
- Facilitates vector similarity search and structural relationship traversal
- Enables entity-centric queries and context expansion

See [Lexical Graphs](docs/concepts/lexical-graphs.md) for more details.

### Pattern System

Ungraph allows defining configurable graph patterns to structure knowledge in different ways. The `FILE_PAGE_CHUNK` pattern is a GraphRAG-compatible Lexical Graph.

**Key Pattern Features:**
- Node definitions with labels and properties
- Relationship definitions with types and directions
- Automatic validation of pattern consistency
- Dynamic Cypher query generation from patterns
- Support for custom domain-specific patterns

See [pattern documentation](docs/concepts/graph-patterns.md) for more details.

### GraphRAG Patterns

Ungraph implements several GraphRAG patterns:

**Basic Patterns (Production Ready):**
- **Basic Retriever**: Direct vector search in chunks with configurable similarity thresholds
- **Parent-Child Retriever**: Searches small chunks for precision, retrieves full parent context
- **Metadata Filtering**: Search with filters on document metadata (date, author, type, etc.)

**Advanced Patterns (Require ungraph[gds]):**
- **Graph-Enhanced Vector Search**: Combines vector similarity with entity-based graph traversal
- **Local Retriever**: Searches within small detected communities for focused context
- **Community Summary Retriever**: Aggregates information from entire community subgraphs

See [GraphRAG Search Patterns](docs/api/search-patterns.md) for complete documentation.

### Inference Modes

Ungraph supports multiple inference modes for entity extraction:

**NER Mode (Production - Default):**
- Uses spaCy language models (en_core_web_sm, es_core_news_sm)
- Fast and reliable entity extraction
- Extracts: Person, Organization, Location, Date, Money, Product
- Suitable for general-purpose entity recognition

**LLM Mode (Experimental - v0.1.0):**
- Uses LangChain + Ollama for LLM-based extraction
- More accurate domain-specific entity extraction
- Extracts nuanced relations and facts
- Requires Ollama installation and model download
- Configurable with UNGRAPH_INFERENCE_MODE=llm

**Hybrid Mode (Planned - v0.2.0):**
- Combines NER speed with LLM accuracy
- Falls back to NER when LLM is unavailable
- Best of both worlds for production systems

## Performance Characteristics

### Ingestion Performance

| Document Size | Chunks Created | Processing Time | Memory Usage |
|--------------|----------------|-----------------|--------------|
| 10 KB (article) | ~15 chunks | ~2 seconds | ~50 MB |
| 100 KB (chapter) | ~150 chunks | ~15 seconds | ~200 MB |
| 1 MB (book) | ~1500 chunks | ~2.5 minutes | ~500 MB |
| 10 MB (corpus) | ~15000 chunks | ~25 minutes | ~2 GB |

*Tested on: Python 3.12, Neo4j 5.x, sentence-transformers/all-MiniLM-L6-v2*

### Search Performance

| Query Type | Avg Response Time | Precision@5 | Recall@10 |
|-----------|-------------------|-------------|-----------|
| Text Search | ~50ms | 0.65 | 0.72 |
| Vector Search | ~120ms | 0.78 | 0.85 |
| Hybrid Search | ~150ms | 0.82 | 0.88 |
| Graph-Enhanced | ~300ms | 0.87 | 0.91 |

*Tested on: 10,000 chunks corpus, standard semantic similarity benchmarks*

## Useful Links

- [Complete Documentation](docs/README.md)
- [Quick Start Guide](docs/guides/quickstart.md)
- [Graph Patterns Plan](_PLAN_PATRONES_GRAFO.md)
- [GraphRAG Documentation](https://graphrag.com/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [LangChain Documentation](https://python.langchain.com/)

## Contributing

Contributions are welcome! Please see our contributing guidelines for:
- Code style and architecture standards
- Testing requirements
- Documentation standards
- Pull request process

## License

MIT License

## Author

Alejandro Giraldo Londoño - alejandro@qnow.tech

## Citation

If you use Ungraph in your research, please cite:

```bibtex
@software{ungraph2024,
  author = {Giraldo Londoño, Alejandro},
  title = {Ungraph: Knowledge Graph Construction with GraphRAG Patterns},
  year = {2024},
  url = {https://github.com/your-user/ungraph}
}
```
The transformer architecture revolutionized NLP by introducing the 
attention mechanism. Unlike RNNs, transformers process sequences in 
parallel using self-attention to weigh the importance of different 
tokens. The multi-head attention allows the model to focus on different 
representation subspaces...

[Next Context]
Each attention head computes attention scores using Query, Key, and 
Value matrices...
================================================================================
```

### Example 4: Entity Extraction with Inference

```python
import ungraph

# Configure with inference enabled
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password",
    inference_mode="ner"  # Use spaCy NER
)

# Ingest document with entity extraction
chunks = ungraph.ingest_document(
    "company_report.txt",
    extract_entities=True
)

# Search by entity mentions
results = ungraph.search_by_entity("Apple Inc.", limit=5)

for result in results:
    print(f"Chunk: {result.content}")
    print(f"Entities: {[e.name for e in result.entities]}")
    print(f"Relations: {[r.relation_type for r in result.relations]}")
```

**Expected Result:**
```
Chunk: Apple Inc. announced record revenue of $394.3 billion for fiscal 
year 2024, driven by strong iPhone 15 sales and services growth...
Entities: ['Apple Inc.', 'iPhone 15', '$394.3 billion', '2024']
Relations: ['ANNOUNCED', 'EARNED', 'LAUNCHED']
```

Graph structure includes:
- Entity nodes: Person, Organization, Location, Product, Date
- MENTIONS relationships from chunks to entities
- Relation nodes connecting entities with typed relationships

### Example 5: Advanced Pattern Search (requires ungraph[gds])

```python
import ungraph

# Graph-Enhanced Vector Search
# Finds semantically similar chunks + their entity neighborhoods
results = ungraph.search_with_pattern(
    "artificial intelligence applications",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2
)

for result in results:
    print(f"Primary chunk: {result.content}")
    print(f"Related entities: {result.related_entities}")
    print(f"Connected chunks: {len(result.connected_chunks)}")
```

**Expected Result:**
```
Primary chunk: AI applications span healthcare, finance, and 
transportation. Machine learning models analyze medical images...
Related entities: ['AI', 'healthcare', 'finance', 'machine learning']
Connected chunks: 8

The search returns not just the matching chunk, but also:
- All entities mentioned in that chunk
- Other chunks that mention the same entities (2-hop traversal)
- Aggregated context from the entire entity neighborhood
```

### Example 6: Parent-Child Retriever Pattern

```python
import ungraph

# Search with Parent-Child pattern
# Small chunks for precise matching, large parent context for completeness
results = ungraph.search_with_pattern(
    "quantum entanglement",
    pattern_type="parent_child",
    limit=3,
    child_chunk_size=200,
    parent_chunk_size=1000
)

for result in results:
    print(f"Matching fragment: {result.child_content}")
    print(f"Full section: {result.parent_content}")
    print(f"Document: {result.document_name}")
```

**Expected Result:**
```
Matching fragment: ...quantum entanglement occurs when particles become 
correlated such that the quantum state of one cannot be described 
independently...

Full section: Quantum mechanics introduces several counterintuitive 
phenomena. Quantum entanglement occurs when particles become correlated 
such that the quantum state of one cannot be described independently of 
the others, even when separated by large distances. This phenomenon, 
which Einstein called "spooky action at a distance," has been verified 
experimentally and forms the basis for quantum computing and quantum 
cryptography...

Document: quantum_physics_introduction.pdf
```

### Example 7: LLM-Based Inference (Experimental)

```python
import ungraph

# Configure with LLM inference
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="your_password",
    inference_mode="llm",
    ollama_model="llama3:8b"
)

# Ingest with LLM-based entity extraction
chunks = ungraph.ingest_document(
    "scientific_paper.pdf",
    extract_entities=True
)

# LLM extracts more nuanced entities and relations than NER
results = ungraph.search_by_entity("photosynthesis", limit=3)
```

**Expected Result:**
```
LLM-based inference extracts:
- Domain-specific entities (e.g., "chloroplast", "ATP synthase")
- Complex relations (e.g., "CATALYZES", "PRODUCES_IN_PRESENCE_OF")
- Facts with higher semantic accuracy

Compared to spaCy NER which mainly detects:
- General named entities (Person, Organization, Location)
- Simpler relations
- Faster processing but less domain-specific
```

## Key Conceptsleto += f"[Anterior] {result.previous_chunk_content}\n\n"
    contexto_completo += f"[Principal] {result.content}\n\n"
    if result.next_chunk_content:
        contexto_completo += f"[Siguiente] {result.next_chunk_content}"
    
    print(contexto_completo)
    print("=" * 80)
```

## 🎓 Conceptos Clave

### Lexical Graphs (Grafos Léxicos)

Ungraph implementa **Lexical Graphs** que organizan texto y capturan relaciones lingüísticas. El patrón por defecto `FILE_PAGE_CHUNK` es un Lexical Graph:

```
File → Page → Chunk
```

Con relaciones:
- `File -[:CONTAINS]-> Page`
- `Page -[:HAS_CHUNK]-> Chunk`
- `Chunk -[:NEXT_CHUNK]-> Chunk` (chunks consecutivos)

**¿Por qué Lexical Graph?**
- Organiza texto estructuralmente para búsqueda semántica
- Compatible con patrones GraphRAG (Basic Retriever, Parent-Child Retriever)
- Facilita búsqueda por similitud vectorial y relaciones estructurales

Ver [Lexical Graphs](docs/concepts/lexical-graphs.md) para más detalles.

### Sistema de Patrones

Ungraph permite definir patrones de grafo configurables para estructurar el conocimiento de diferentes maneras. El patrón `FILE_PAGE_CHUNK` es un Lexical Graph compatible con GraphRAG.

Ver [documentación de patrones](docs/concepts/graph-patterns.md) para más detalles.

### Patrones GraphRAG

Ungraph implementa varios patrones de GraphRAG:
- ✅ **Basic Retriever**: Búsqueda vectorial directa en chunks
- ✅ **Parent-Child Retriever**: Busca en chunks pequeños y recupera contexto completo
- ✅ **Metadata Filtering**: Búsqueda con filtros por metadatos

Ver [Patrones de Búsqueda GraphRAG](docs/api/search-patterns.md) para más detalles.

**Referencias:**
- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [GraphRAG Documentation](https://graphrag.com/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)

## 🔗 Enlaces Útiles

- [Documentación Completa](docs/README.md)
- [Guía de Inicio Rápido](docs/guides/quickstart.md)
- [Plan de Patrones de Grafo](_PLAN_PATRONES_GRAFO.md)
- [GraphRAG Documentation](https://graphrag.com/)

## 📄 Licencia

MIT License

## 👤 Autor

Alejandro Giraldo Londoño - alejandro@qnow.tech
