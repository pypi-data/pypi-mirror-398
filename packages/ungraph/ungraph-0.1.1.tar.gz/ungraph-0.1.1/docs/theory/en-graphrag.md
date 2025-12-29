# GraphRAG: Theoretical Foundations

## What is GraphRAG?

GraphRAG (Graph Retrieval-Augmented Generation) is an advanced RAG approach that uses knowledge graphs to improve information retrieval and generation.

**Core idea**: Leverage relationships between data to be retrieved in RAG. Instead of only searching by vector similarity, GraphRAG uses the graph structure to enrich search and retrieval.

## Fundamental Concepts

### Traditional RAG vs GraphRAG

**Traditional RAG:**
- Uses simple vector search
- Does not consider relationships between documents
- Limited to semantic similarity

**GraphRAG:**
- Uses graph structure to enrich search
- Considers relationships between entities
- Combines multiple signals (text, vector, structure)

## Types of Graphs in GraphRAG

### Lexical Graphs

Structures that organize text and capture linguistic relationships. They focus on language structure and facilitate semantic search.

**Characteristics**:
- Organize text into related chunks
- Contain embeddings for semantic search
- Structural relationships (CONTAINS, HAS_CHUNK, NEXT_CHUNK)
- Compatible with basic GraphRAG patterns

**In Ungraph**: The `FILE_PAGE_CHUNK` pattern is a Lexical Graph. See [Lexical Graphs](../concepts/en-lexical-graphs.md) for more details.

### Knowledge Graphs

Structures that represent factual knowledge and relationships between domain entities. They focus on verifiable facts and structured schemas.

**Characteristics**:
- Represent domain entities and relationships
- Known structured schemas
- Semantic relationships (AUTHORED_BY, PART_OF, etc.)
- Require special strategies for retrieval (Cypher Templates, Dynamic Generation)

## GraphRAG Search Patterns

### 1. Basic Retriever

**Also known as**: Naive Retriever, Basic RAG, Typical RAG

**Required graph pattern**: Lexical Graph

**How it works**:
- The user's question is vectorized using the same embedding model as the chunks
- Similarity search is executed on chunk embeddings
- The `k` most similar chunks are retrieved

**When to use**: When the requested information is in specific nodes related to topics distributed in one or more chunks, but not in a large number of them.

**No additional query required**: Similarity search is performed directly on the nodes.

**Reference:** [GraphRAG Basic Retriever](https://graphrag.com/reference/graphrag/basic-retriever/)

### 2. Parent-Child Retriever

**Also known as**: Parent-Document Retriever

**Required graph pattern**: Lexical Graph with hierarchical structure

**Evolution of Lexical Graph**: Splits large documents into smaller parts (chunks) to create more meaningful embeddings. Creates a hierarchy where:
- **Small chunks (children)**: Contain embedded text and embeddings (better vector representation)
- **Large chunks (parents)**: Only used for context in response generation

**Relationships**: `PART_OF`, `HAS_CHILD`

**How it works**:
- Search in small chunks (better vector matching, less noise)
- Retrieve parent chunk (full context for generation)

**When to use**: When many topics in a chunk negatively affect vector quality, but you need full context to generate responses.

**Reference:** [GraphRAG Parent-Child Retriever](https://graphrag.com/reference/graphrag/parent-child-retriever/)

### 3. Hypothetical Question Retriever

**Idea**: Generate hypothetical questions for each chunk using an LLM to improve matching between user questions and available content.

**How it works**:
- An LLM is used to generate questions and answers for each chunk
- Similarity search is performed on the generated questions
- The most similar questions are found and corresponding chunks are returned

**When to use**: When similarity between user question vectors and chunk vectors is low. This procedure increases similarity between user and available text.

**Requirement**: Requires more LLM processing as it needs to generate questions per chunk.

**Reference:** [GraphRAG Hypothetical Question Retriever](https://graphrag.com/reference/graphrag/hypothetical-question-retriever/)

### 4. Community Summary Retriever

Finds communities of related nodes and generates summaries.

**Reference:** [GraphRAG Community Summary Retriever](https://graphrag.com/reference/graphrag/community-summary-retriever/)

### 5. Graph-Enhanced Vector Search

Combines vector search with graph structure.

**Reference:** [GraphRAG Graph-Enhanced Vector Search](https://graphrag.com/reference/graphrag/graph-enhanced-vector-search/)

### 6. Domain Graphs

Structured graphs with known schemas. We cannot know in advance what structure the entities will have, often they follow a structure from structured data (like when mapping from a relational database to the graph).

**Retrieval strategies**:
- **Cypher Templates**: Set of default queries that can be populated from user questions. The LLM extracts parameters and decides which template to use.
- **Dynamic Cypher Generation**: The LLM dynamically generates Cypher queries based on the user's question.

**When to use**: When you have structured data with known schemas and need deterministic retrieval of structured data.

## Research and Papers

### Main Papers

1. **Retrieval-Augmented Generation with Graphs (GraphRAG)**
   - Microsoft Research
   - [Link](https://graphrag.com/appendices/research/)

2. **Graph Retrieval-Augmented Generation: A Survey**
   - Complete state-of-the-art review
   - [Link](https://graphrag.com/appendices/research/)

### Key Concepts from Papers

- **Knowledge Graphs**: Explicit knowledge structure
- **Graph Traversal**: Navigation through graph relationships
- **Community Detection**: Identification of related communities
- **Hybrid Retrieval**: Combination of multiple signals

## Applications

### Use Cases

1. **Technical Documentation**: Semantic search in documentation
2. **Academic Research**: Exploration of related papers
3. **Knowledge Bases**: Enterprise knowledge bases
4. **Q&A Systems**: Enhanced question-answering systems

## References

- [GraphRAG Documentation](https://graphrag.com/)
- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [GraphRAG Research Papers](https://graphrag.com/appendices/research/)
- [Neo4j GraphRAG Guide](https://go.neo4j.com/rs/710-RRC-335/images/Developers-Guide-GraphRAG.pdf)
