# Lexical Graphs

## What is a Lexical Graph according to GraphRAG?

A **Lexical Graph** (according to GraphRAG's definition) is a data structure that organizes **text into chunks** with `PART_OF` relationships. It's used for basic semantic search in GraphRAG systems.

**Important**: Don't confuse with "linguistic lexical graphs" that represent relationships between words (synonyms, antonyms, etc.). A GraphRAG Lexical Graph is a structure of text chunks, not individual words.

### Key Characteristics

- **Focus**: Structural organization of text into chunks
- **Relationships**: `PART_OF` (or equivalents like `CONTAINS`, `HAS_CHUNK`) between chunks and documents
- **Purpose**: Facilitate semantic search using embeddings and text structure
- **Usage**: Basic GraphRAG patterns like Basic Retriever and Parent-Child Retriever

### Typical Structure

```
Document -[:PART_OF]-> Chunk
Chunk -[:NEXT_CHUNK]-> Chunk  (to maintain sequence)
```

## Lexical Graph vs Knowledge Graph

It's important to differentiate between these two concepts:

| Aspect | Lexical Graph (GraphRAG) | Knowledge Graph |
|---------|-------------------------|-----------------|
| **Focus** | Text chunk structure | Structured factual knowledge |
| **Relationships** | Structural (PART_OF, NEXT_CHUNK) | Domain semantics (AUTHORED_BY, PART_OF, etc.) |
| **Example** | Document → Chunk → Chunk (sequence) | "Einstein" → "authored" → "Relativity" |
| **GraphRAG Use** | Basic search (Basic Retriever) | Advanced search (Graph-Enhanced Vector Search) |

### Comparative Example

**Lexical Graph (GraphRAG)**:
```
File:document.md -[:CONTAINS]-> Page:1 -[:HAS_CHUNK]-> Chunk:1
Chunk:1 -[:NEXT_CHUNK]-> Chunk:2
Chunk:2 contains text about "machine learning"
```

**Knowledge Graph (Domain Graph)**:
```
Person:Einstein -[:AUTHORED]-> Paper:Relativity
Paper:Relativity -[:CITES]-> Paper:Quantum_Mechanics
```

**Key difference**: Lexical Graph organizes text structurally (chunks), while Knowledge Graph represents factual knowledge (entities and domain relationships).

## Lexical Graphs in Ungraph

### The FILE_PAGE_CHUNK Pattern is a Lexical Graph

In Ungraph, the `FILE_PAGE_CHUNK` pattern implements a **Lexical Graph (according to GraphRAG)** because:

1. **Organizes text structurally**: Splits documents into related chunks
2. **Captures structural relationships**: Chunks are connected by relationships reflecting the text structure (CONTAINS, HAS_CHUNK, NEXT_CHUNK)
3. **Facilitates semantic search**: Embeddings in each chunk enable semantic similarity search

### Lexical Graph Structure in Ungraph

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                              Chunk -[:NEXT_CHUNK]-> Chunk
```

**Characteristics**:
- **File**: Represents the source document
- **Page**: Represents pages/sections of the document
- **Chunk**: Contains text and embeddings (semantic representation)
- **Relationships**: Structure text hierarchically and sequentially

### Chunk Properties (Lexical Graph Nodes)

Each `Chunk` node contains:
- `page_content`: The chunk's text
- `embeddings`: Vector representation of the text (semantic similarity)
- `chunk_id`: Unique identifier
- `chunk_id_consecutive`: Sequential order

These properties enable:
- **Vector search**: Using embeddings to find semantically similar chunks
- **Text search**: Using `page_content` for full-text search
- **Sequential navigation**: Using `NEXT_CHUNK` to traverse the document

## Using Lexical Graphs in GraphRAG

### Pattern: Basic Retriever

The **Basic Retriever** requires a Lexical Graph because:

1. **Vectorizes the question**: Uses the same embedding model as the chunks
2. **Searches for similarity**: Finds the k most similar chunks using embeddings
3. **Returns text**: Returns the `page_content` of the found chunks

**Example**:
```python
# The question is vectorized
query_embedding = embedding_service.generate_embedding("What is machine learning?")

# Similarity search in chunk embeddings
results = search_service.vector_search(query_embedding, limit=5)

# Return most similar chunks
for result in results:
    print(result.content)  # chunk's page_content
```

### Pattern: Parent-Child Retriever

The **Parent-Child Retriever** is an evolution of the Lexical Graph:

- **Small chunks (children)**: Better vector representation (less noise)
- **Large chunks (parents)**: Full context for generation

**Structure**:
```
Page (parent) -[:HAS_CHILD]-> Chunk (child)
Chunk (child) -[:PART_OF]-> Page (parent)
```

**Flow**:
1. Search in small chunks (better vector matching)
2. Retrieve parent chunk (full context)
3. Use full context to generate response

## When to Use Lexical Graphs

### ✅ Use Lexical Graph when:

- You need to organize unstructured text
- You want semantic search in documents
- Documents have hierarchical structure (pages, sections)
- You need to maintain sequential text order
- You want to implement basic GraphRAG patterns (Basic Retriever, Parent-Child)

### ❌ Don't use Lexical Graph when:

- You need to represent structured factual knowledge
- Relationships are between domain entities (people, places, concepts)
- You need a fixed knowledge schema
- You want to represent verifiable facts

In these cases, consider using a **Knowledge Graph** (Domain Graph).

## Practical Example

### Create a Lexical Graph with Ungraph

```python
import ungraph

# Ingest document (creates Lexical Graph automatically)
chunks = ungraph.ingest_document(
    "document.md",
    chunk_size=1000,
    chunk_overlap=200
)

# The created graph is a Lexical Graph:
# File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
#                              Chunk -[:NEXT_CHUNK]-> Chunk

# Search using Basic Retriever (requires Lexical Graph)
results = ungraph.search("machine learning", limit=5)

# Each result is a chunk from the Lexical Graph
for result in results:
    print(f"Chunk ID: {result.chunk_id}")
    print(f"Content: {result.content[:200]}...")
    print(f"Score: {result.score}")
```

### Visualize the Lexical Graph

```cypher
// View Lexical Graph structure
MATCH path = (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN path
LIMIT 50

// View sequential relationships
MATCH path = (c1:Chunk)-[:NEXT_CHUNK]->(c2:Chunk)
RETURN path
LIMIT 20
```

## References

- [GraphRAG - Lexical Graphs](https://graphrag.com/reference/knowledge-graph/lexical-graph/)
- [Graph Patterns in Ungraph](./en-graph-patterns.md)
- [GraphRAG Search Patterns](../api/en-search-patterns.md)
- [Lexical Graph - Concepts](../../src/notebooks/Grafo%20Léxico.md)
