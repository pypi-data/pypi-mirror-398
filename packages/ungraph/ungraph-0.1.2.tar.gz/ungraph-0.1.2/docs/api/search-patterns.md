> Documento movido / Document moved

Este documento ahora está disponible en versiones bilingües:

- Español: [sp-search-patterns.md](sp-search-patterns.md)
- English: [en-search-patterns.md](en-search-patterns.md)

Por favor actualiza tus enlaces y marcadores a una de las versiones anteriores.

Please update your links/bookmarks to one of the above versions.

## Introducción

Los patrones de búsqueda GraphRAG permiten recuperar información del grafo de conocimiento usando diferentes estrategias, cada una optimizada para diferentes tipos de consultas.

**Concepto clave**: Estos patrones aprovechan la estructura del grafo (especialmente **Lexical Graphs**) para mejorar la recuperación de información. En lugar de buscar solo por similitud vectorial, GraphRAG utiliza las relaciones entre nodos para enriquecer los resultados.

**En Ungraph**: El patrón `FILE_PAGE_CHUNK` es un Lexical Graph que soporta estos patrones de búsqueda. Ver [Lexical Graphs](../concepts/lexical-graphs.md) para más detalles.

**Referencias:**
- [GraphRAG Retrieval Patterns](https://graphrag.com/reference/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Lexical Graphs en Ungraph](../concepts/lexical-graphs.md)

## Patrones Disponibles

### ✅ 1. Basic Retriever (IMPLEMENTADO)

**También conocido como**: Recuperador Ingenuo, RAG Básico, RAG Típico

**Patrón de grafo requerido**: Lexical Graph (como `FILE_PAGE_CHUNK`)

**Estado:** ✅ **IMPLEMENTADO Y DISPONIBLE**

**Cómo funciona**:
1. La pregunta del usuario se vectoriza usando el mismo modelo de embeddings que los chunks
2. Se ejecuta búsqueda de similitud en los embeddings de los chunks
3. Se recuperan los `k` chunks más similares directamente desde los nodos

**Cuándo usar:**
- La información solicitada se encuentra en nodos específicos relacionados con temas distribuidos en uno o más chunks
- No necesitas contexto adicional más allá del chunk encontrado
- Búsquedas por palabras clave o conceptos simples
- Cuando la similitud entre pregunta y contenido es alta

**Cuándo NO usar:**
- Cuando necesitas contexto completo de una sección (usa Parent-Child)
- Cuando la información está distribuida en muchos chunks relacionados (considera Community Summary)
- Cuando necesitas filtrar por metadatos específicos (usa Metadata Filtering)

**Ejemplo:**
```python
import ungraph

results = ungraph.search_with_pattern(
    "inteligencia artificial",
    pattern_type="basic",
    limit=5
)
```

**Query Cypher generado:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
RETURN node.page_content as content, score
ORDER BY score DESC
LIMIT $limit
```

---

### ✅ 2. Metadata Filtering (IMPLEMENTADO)

Búsqueda full-text con filtros por metadatos.

**Estado:** ✅ **IMPLEMENTADO Y DISPONIBLE**

**Cuándo usar:**
- Buscar solo en documentos específicos
- Filtrar por fecha, autor, tipo de documento, etc.
- Reducir el espacio de búsqueda para mayor precisión

**Ejemplo:**
```python
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md",
        "page_number": 1
    },
    limit=10
)
```

**Query Cypher generado:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
WHERE node.filename = $filename AND node.page_number = $page_number
RETURN node.page_content as content, score
ORDER BY score DESC
LIMIT $limit
```

---

### ✅ 3. Parent-Child Retriever (IMPLEMENTADO)

**También conocido como**: Recuperador Padre-Documento

**Patrón de grafo requerido**: Lexical Graph con estructura jerárquica

**Estado:** ✅ **IMPLEMENTADO Y DISPONIBLE**

**Cómo funciona**:
Este patrón es una evolución del Lexical Graph básico:
- **Chunks pequeños (hijos)**: Contienen texto embebido y embeddings (mejor representación vectorial, menos ruido)
- **Chunks grandes (padres)**: Solo se usan para contexto en generación de respuestas

**Flujo**:
1. Busca en chunks pequeños usando búsqueda vectorial (mejor matching)
2. Recupera el chunk padre relacionado (contexto completo)
3. Usa el contexto completo para generar respuesta

**Cuándo usar:**
- Cuando muchos temas en un chunk afectan negativamente la calidad de los vectores
- Necesitas contexto completo de una sección para generar respuestas
- Los chunks pequeños tienen mejor representación vectorial pero falta contexto
- Buscar en Pages y obtener todos sus Chunks relacionados

**Cuándo NO usar:**
- Cuando un chunk pequeño contiene suficiente información (usa Basic Retriever)
- Cuando no tienes estructura jerárquica padre-hijo en tu grafo

**Ejemplo:**
```python
results = ungraph.search_with_pattern(
    "computación cuántica",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=5
)

# Resultados incluyen Page y todos sus Chunks
for result in results:
    print(f"Page: {result.parent_content}")
    print(f"Chunks relacionados: {len(result.children)}")
```

**Query Cypher generado:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as parent_node, score as parent_score

OPTIONAL MATCH (parent_node:Page)-[:HAS_CHUNK]->(child_node:Chunk)

RETURN {
    parent_content: parent_node.page_content,
    parent_score: parent_score,
    children: collect(DISTINCT {
        content: child_node.page_content,
        chunk_id: child_node.chunk_id
    })
} as result
ORDER BY parent_score DESC
LIMIT $limit
```

---

### ✅ 4. Community Summary Retriever (GDS) (IMPLEMENTADO - Requiere ungraph[gds])

Encuentra comunidades de nodos relacionados y genera resúmenes usando Graph Data Science.

**Estado:** ✅ **IMPLEMENTADO Y DISPONIBLE** (requiere `pip install ungraph[gds]` y Neo4j GDS plugin)

**Ver documentación completa**: [Patrones Avanzados de Búsqueda](../api/advanced-search-patterns.md)

**Cuándo usar:**
- Necesitas contexto amplio sobre un tema
- Buscar información relacionada en el grafo
- Generar resúmenes de conocimiento

**Ejemplo:**
```python
results = ungraph.search_with_pattern(
    "deep learning",
    pattern_type="community",
    community_threshold=5,  # Mínimo 5 nodos relacionados
    max_depth=2,  # Profundidad máxima de relaciones
    limit=3
)

for result in results:
    print(f"Chunk central: {result.central_content[:100]}...")
    print(f"Tamaño de comunidad: {result.community_size}")
    print(f"Resumen: {result.community_summary[:200]}...")
```

**Query Cypher generado:**
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as central_node, score

MATCH path = (central_node)-[*1..2]-(community_node:Chunk)
WHERE community_node <> central_node

WITH central_node, score,
     collect(DISTINCT community_node) as community,
     count(DISTINCT community_node) as community_size

WHERE community_size >= $community_threshold

RETURN {
    central_content: central_node.page_content,
    central_score: score,
    community_size: community_size,
    community_summary: reduce(
        summary = "",
        node IN community |
        summary + " " + coalesce(node.page_content, "")
    )
} as result
ORDER BY score DESC, community_size DESC
LIMIT $limit
```

---

### ✅ 5. Local Retriever (IMPLEMENTADO - Requiere ungraph[gds])

Similar a Community Summary pero optimizado para comunidades pequeñas.

**Estado:** ✅ **IMPLEMENTADO Y DISPONIBLE** (requiere `pip install ungraph[gds]`)

**Ver documentación completa**: [Patrones Avanzados de Búsqueda](../api/advanced-search-patterns.md)

**Cuándo usar:**
- Exploración de conocimiento específico
- Comunidades más pequeñas y focalizadas
- Cuando Community Summary retorna demasiados resultados

**Ejemplo:**
```python
results = ungraph.search_with_pattern(
    "neural networks",
    pattern_type="local",
    local_threshold=3,  # Threshold más bajo
    max_depth=1,  # Profundidad menor
    limit=5
)
```

---

### ✅ 6. Graph-Enhanced Vector Search (IMPLEMENTADO - Requiere ungraph[gds])

Combina búsqueda vectorial (semántica) con estructura del grafo.

**Estado:** ✅ **IMPLEMENTADO Y DISPONIBLE** (requiere `pip install ungraph[gds]`)

**Ver documentación completa**: [Patrones Avanzados de Búsqueda](../api/advanced-search-patterns.md)

**Cuándo usar:**
- Necesitas similitud semántica Y contexto estructural
- Quieres considerar relaciones del grafo en la búsqueda
- Búsquedas más sofisticadas que combinan múltiples señales

**Ejemplo:**
```python
from ungraph import HuggingFaceEmbeddingService

# Generar embedding de la query
embedding_service = HuggingFaceEmbeddingService()
query_embedding = embedding_service.generate_embedding("deep learning")

# Búsqueda Graph-Enhanced Vector
results = ungraph.search_with_pattern(
    "deep learning",
    pattern_type="graph_enhanced_vector",
    query_vector=query_embedding.vector,
    relationship_types=["NEXT_CHUNK", "HAS_CHUNK"],
    limit=5
)

for result in results:
    print(f"Score combinado: {result.combined_score}")
    print(f"Chunks relacionados: {result.related_count}")
```

**Query Cypher generado:**
```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $query_vector)
YIELD node as vec_node, score as vec_score

OPTIONAL MATCH path = (vec_node)-[:NEXT_CHUNK|HAS_CHUNK]*1..2-(related_node:Chunk)
WHERE related_node IS NOT NULL

WITH vec_node, vec_score,
     collect(DISTINCT related_node) as related_nodes,
     count(DISTINCT related_node) as related_count

CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as text_node, score as text_score
WHERE text_node = vec_node

RETURN {
    content: vec_node.page_content,
    vector_score: vec_score,
    text_score: text_score,
    combined_score: (vec_score * 0.6 + text_score * 0.4),
    chunk_id: vec_node.chunk_id,
    related_count: related_count
} as result
ORDER BY result.combined_score DESC
LIMIT $limit
```

---

## Comparación de Patrones

| Patrón | Estado | Velocidad | Precisión | Contexto | Uso Recomendado |
|--------|--------|-----------|-----------|----------|------------------|
| Basic | ✅ Implementado | ⚡⚡⚡ | ⭐⭐ | ⭐ | Búsquedas simples |
| Metadata Filtering | ✅ Implementado | ⚡⚡⚡ | ⭐⭐⭐ | ⭐ | Búsquedas filtradas |
| Parent-Child | ✅ Implementado | ⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | Contexto jerárquico |
| Community Summary | ✅ Implementado* | ⚡ | ⭐⭐ | ⭐⭐⭐⭐ | Resúmenes amplios |
| Local | ✅ Implementado* | ⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | Exploración focalizada |
| Graph-Enhanced Vector | ✅ Implementado* | ⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Búsquedas avanzadas |

*Requiere `pip install ungraph[gds]`. Ver [Patrones Avanzados](../api/advanced-search-patterns.md)

## Mejores Prácticas

1. **Empezar simple**: Usa `basic` o `metadata_filtering` primero (✅ Disponibles)
2. **Ajustar según necesidad**: Si necesitas más contexto, usa `parent_child` (✅ Disponible)
3. **Considerar performance**: Los patrones avanzados (`community`, `graph_enhanced_vector`) son más lentos pero proporcionan mejor contexto (✅ Disponibles con `ungraph[gds]`)
4. **Filtrar cuando sea posible**: Usa `metadata_filtering` para reducir espacio de búsqueda (✅ Disponible)
5. **Combinar patrones**: Puedes ejecutar múltiples búsquedas y combinar resultados

## Requisitos

**Índices requeridos en Neo4j:**
- `chunk_content`: Índice full-text para búsqueda de texto completo
  - Se crea automáticamente con `ungraph.ingest_document()` o `index_service.setup_all_indexes()`

**Nota:** Los patrones básicos (✅) están siempre disponibles. Los patrones avanzados (✅*) requieren `pip install ungraph[gds]` y están documentados en [Patrones Avanzados de Búsqueda](../api/advanced-search-patterns.md).

## Referencias

- [GraphRAG Retrieval Patterns](https://graphrag.com/reference/)
- [Neo4j Full-Text Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [GraphRAG Research Papers](https://graphrag.com/appendices/research/)


