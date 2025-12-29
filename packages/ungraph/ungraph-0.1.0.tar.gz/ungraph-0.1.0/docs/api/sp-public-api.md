# API Pública de Ungraph

Referencia completa de la API pública de Ungraph.

## Funciones Principales

### `ingest_document()`

Ingiere un documento al grafo de conocimiento.

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

**Parámetros:**
- `file_path`: Ruta al archivo a ingerir
- `chunk_size`: Tamaño de cada chunk (default: 1000)
- `chunk_overlap`: Solapamiento entre chunks (default: 200)
- `clean_text`: Limpiar texto antes de procesar (default: True)
- `database`: Nombre de la base de datos Neo4j (default: desde configuración)
- `embedding_model`: Modelo de embedding a usar (default: desde configuración)

**Retorna:** Lista de objetos `Chunk` creados

**Ejemplo:**
```python
import ungraph

chunks = ungraph.ingest_document("documento.md", chunk_size=500)
print(f"Creados {len(chunks)} chunks")
```

---

### `search()`

Busca en el grafo usando búsqueda por texto.

```python
results = ungraph.search(
    query_text: str,
    limit: int = 5,
    database: Optional[str] = None
) -> List[SearchResult]
```

**Parámetros:**
- `query_text`: Texto a buscar
- `limit`: Número máximo de resultados (default: 5)
- `database`: Nombre de la base de datos Neo4j (default: desde configuración)

**Retorna:** Lista de `SearchResult` ordenados por score descendente

**Ejemplo:**
```python
results = ungraph.search("computación cuántica", limit=10)
for result in results:
    print(f"Score: {result.score}, Content: {result.content[:100]}")
```

---

### `hybrid_search()`

Búsqueda híbrida combinando texto y vectorial.

```python
results = ungraph.hybrid_search(
    query_text: str,
    limit: int = 5,
    weights: Tuple[float, float] = (0.3, 0.7),
    database: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> List[SearchResult]
```

**Parámetros:**
- `query_text`: Texto a buscar
- `limit`: Número máximo de resultados (default: 5)
- `weights`: Pesos para combinar scores `(text_weight, vector_weight)` (default: (0.3, 0.7))
- `database`: Nombre de la base de datos Neo4j (default: desde configuración)
- `embedding_model`: Modelo de embedding a usar (default: desde configuración)

**Retorna:** Lista de `SearchResult` ordenados por score combinado descendente

**Ejemplo:**
```python
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.4, 0.6)  # 40% texto, 60% vectorial
)
```

---

### `suggest_chunking_strategy()`

Obtiene recomendación inteligente de estrategia de chunking.

```python
recommendation = ungraph.suggest_chunking_strategy(
    file_path: str | Path
) -> ChunkingRecommendation
```

**Parámetros:**
- `file_path`: Ruta al archivo a analizar

**Retorna:** Objeto `ChunkingRecommendation` con:
- `strategy`: Nombre de la estrategia recomendada
- `chunk_size`: Tamaño de chunk recomendado
- `chunk_overlap`: Solapamiento recomendado
- `explanation`: Explicación de la recomendación
- `quality_score`: Score de calidad (0-1)
- `alternatives`: Lista de alternativas evaluadas

**Ejemplo:**
```python
recommendation = ungraph.suggest_chunking_strategy("documento.md")
print(f"Usar: chunk_size={recommendation.chunk_size}, overlap={recommendation.chunk_overlap}")
```

---

### `configure()`

Configuración programática de Ungraph.

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

**Parámetros:**
- `neo4j_uri`: URI de conexión a Neo4j
- `neo4j_user`: Usuario de Neo4j
- `neo4j_password`: Contraseña de Neo4j
- `neo4j_database`: Nombre de la base de datos
- `embedding_model`: Modelo de embedding a usar
- `**kwargs`: Otros parámetros de configuración

**Ejemplo:**
```python
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="mi_contraseña",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

---

## Clases Principales

### `Chunk`

Entidad que representa un fragmento de texto.

```python
@dataclass
class Chunk:
    id: str
    page_content: str
    metadata: Dict[str, Any]
```

**Atributos:**
- `id`: Identificador único del chunk
- `page_content`: Contenido del chunk
- `metadata`: Metadatos adicionales

---

### `SearchResult`

Resultado de una búsqueda.

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

**Atributos:**
- `content`: Contenido del chunk encontrado
- `score`: Score de relevancia
- `chunk_id`: ID del chunk
- `chunk_id_consecutive`: Número consecutivo del chunk
- `previous_chunk_content`: Contenido del chunk anterior (si existe)
- `next_chunk_content`: Contenido del chunk siguiente (si existe)

---

### `ChunkingRecommendation`

Recomendación de estrategia de chunking.

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

**Atributos:**
- `strategy`: Nombre de la estrategia recomendada
- `chunk_size`: Tamaño de chunk recomendado
- `chunk_overlap`: Solapamiento recomendado
- `explanation`: Explicación textual
- `quality_score`: Score de calidad (0-1)
- `alternatives`: Alternativas evaluadas

---

## Módulos Disponibles

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

### Servicios

```python
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService
from infrastructure.services.neo4j_search_service import Neo4jSearchService
```

## Referencias

- [Guía de Inicio Rápido](../guides/sp-quickstart.md)
- [Guía de Ingesta](../guides/sp-ingestion.md)
- [Guía de Búsqueda](../guides/search.md)
