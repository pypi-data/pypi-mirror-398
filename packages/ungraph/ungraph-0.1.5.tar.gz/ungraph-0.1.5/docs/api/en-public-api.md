# Ungraph Public API

Complete reference for the Ungraph public API.

## Core Functions

### `ingest_document()`

Ingests a document into the knowledge graph.

```python
chunks = ungraph.ingest_document(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    clean_text: bool = True,
    database: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> List[Chunk]
```

**Parameters:**
- `file_path`: Path to the file to ingest
- `chunk_size`: Size of each chunk (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 200)
- `clean_text`: Clean text before processing (default: True)
- `database`: Neo4j database name (default: from configuration)
- `embedding_model`: Embedding model to use (default: from configuration)

**Returns:** List of created `Chunk` objects

**Example:**
```python
import ungraph

chunks = ungraph.ingest_document("document.md", chunk_size=500)
print(f"Created {len(chunks)} chunks")
```

---

### `search()`

Performs text-based search over the graph.

```python
results = ungraph.search(
    query_text: str,
    limit: int = 5,
    database: Optional[str] = None
) -> List[SearchResult]
```

**Parameters:**
- `query_text`: Text to search for
- `limit`: Maximum number of results (default: 5)
- `database`: Neo4j database name (default: from configuration)

**Returns:** List of `SearchResult` sorted by descending score

**Example:**
```python
results = ungraph.search("quantum computing", limit=10)
for result in results:
    print(f"Score: {result.score}, Content: {result.content[:100]}")
```

---

### `hybrid_search()`

Hybrid search combining text and vector signals.

```python
results = ungraph.hybrid_search(
    query_text: str,
    limit: int = 5,
    weights: Tuple[float, float] = (0.3, 0.7),
    database: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> List[SearchResult]
```

**Parameters:**
- `query_text`: Text to search for
- `limit`: Maximum number of results (default: 5)
- `weights`: Combination weights `(text_weight, vector_weight)` (default: (0.3, 0.7))
- `database`: Neo4j database name (default: from configuration)
- `embedding_model`: Embedding model to use (default: from configuration)

**Returns:** List of `SearchResult` sorted by combined score

**Example:**
```python
results = ungraph.hybrid_search(
    "artificial intelligence",
    limit=10,
    weights=(0.4, 0.6)
)
```

---

### `suggest_chunking_strategy()`

Gets a smart recommendation for chunking strategy.

```python
recommendation = ungraph.suggest_chunking_strategy(
    file_path: str | Path
) -> ChunkingRecommendation
```

**Parameters:**
- `file_path`: Path to the file to analyze

**Returns:** `ChunkingRecommendation` with:
- `strategy`: Recommended strategy name
- `chunk_size`: Recommended chunk size
- `chunk_overlap`: Recommended overlap
- `explanation`: Reasoning behind the recommendation
- `quality_score`: Quality score (0-1)
- `alternatives`: Evaluated alternatives

**Example:**
```python
recommendation = ungraph.suggest_chunking_strategy("document.md")
print(f"Use: chunk_size={recommendation.chunk_size}, overlap={recommendation.chunk_overlap}")
```

---

### `configure()`

Programmatic configuration of Ungraph.

```python
ungraph.configure(
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None,
    neo4j_database: Optional[str] = None,
    embedding_model: Optional[str] = None,
    **kwargs
) -> None
```

**Parameters:**
- `neo4j_uri`: Neo4j connection URI
- `neo4j_user`: Neo4j user
- `neo4j_password`: Neo4j password
- `neo4j_database`: Database name
- `embedding_model`: Embedding model to use
- `**kwargs`: Additional configuration parameters

**Example:**
```python
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="my_password",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

---

## Core Classes

### `Chunk`

Represents a text fragment.

```python
@dataclass
class Chunk:
    id: str
    page_content: str
    metadata: Dict[str, Any]
```

**Attributes:**
- `id`: Unique chunk identifier
- `page_content`: Chunk content
- `metadata`: Additional metadata

---

### `SearchResult`

Represents a search result.

```python
@dataclass
class SearchResult:
    content: str
    score: float
    chunk_id: str
    chunk_id_consecutive: int = 0
    previous_chunk_content: Optional[str] = None
    next_chunk_content: Optional[str] = None
```

**Attributes:**
- `content`: Content of the matched chunk
- `score`: Relevance score
- `chunk_id`: Chunk ID
- `chunk_id_consecutive`: Consecutive number of the chunk
- `previous_chunk_content`: Previous chunk content (if present)
- `next_chunk_content`: Next chunk content (if present)

---

### `ChunkingRecommendation`

Chunking strategy recommendation.

```python
@dataclass
class ChunkingRecommendation:
    strategy: str
    chunk_size: int
    chunk_overlap: int
    explanation: str
    quality_score: float
    alternatives: List[ChunkingStrategy]
```

**Attributes:**
- `strategy`: Recommended strategy name
- `chunk_size`: Recommended chunk size
- `chunk_overlap`: Recommended overlap
- `explanation`: Text explanation
- `quality_score`: Quality score (0-1)
- `alternatives`: Evaluated alternatives

---

## Modules

### Value Objects

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition
)

from domain.value_objects.predefined_patterns import (
    FILE_PAGE_CHUNK_PATTERN
)
```

### Services

```python
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService
from infrastructure.services.neo4j_search_service import Neo4jSearchService
```

## References

- [Quickstart Guide](../guides/en-quickstart.md)
- [Ingestion Guide](../guides/en-ingestion.md)
- [Search Guide](../guides/search.md)
