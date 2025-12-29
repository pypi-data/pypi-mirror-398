# Patrones de Búsqueda GraphRAG

## Introducción

Los patrones de búsqueda GraphRAG permiten recuperar información del grafo de conocimiento usando diferentes estrategias, cada una optimizada para diferentes tipos de consultas.

**Concepto clave**: Estos patrones aprovechan la estructura del grafo (especialmente **Lexical Graphs**) para mejorar la recuperación de información. En lugar de buscar solo por similitud vectorial, GraphRAG utiliza las relaciones entre nodos para enriquecer los resultados.

**En Ungraph**: El patrón `FILE_PAGE_CHUNK` es un Lexical Graph que soporta estos patrones de búsqueda. Ver [Lexical Graphs](../concepts/sp-lexical-graphs.md) para más detalles.

**Referencias:**
- [GraphRAG Retrieval Patterns](https://graphrag.com/reference/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Lexical Graphs en Ungraph](../concepts/sp-lexical-graphs.md)

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

**Ver documentación completa**: [Patrones Avanzados de Búsqueda](../api/sp-advanced-search-patterns.md)

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
```
