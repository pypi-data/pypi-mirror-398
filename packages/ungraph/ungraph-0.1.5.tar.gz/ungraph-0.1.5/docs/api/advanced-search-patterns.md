> Documento movido / Document moved

Este documento ahora está disponible en versiones bilingües:

- Español: [sp-advanced-search-patterns.md](sp-advanced-search-patterns.md)
- English: [en-advanced-search-patterns.md](en-advanced-search-patterns.md)

Por favor actualiza tus enlaces y marcadores a una de las versiones anteriores.

Please update your links/bookmarks to one of the above versions.

## Patrones Avanzados Disponibles

### 1. Graph-Enhanced Vector Search ⭐ RECOMENDADO

**Requisitos**: `ungraph[gds]` y entidades extraídas en el grafo

**Cómo funciona**:
1. Busca chunks similares usando embeddings (búsqueda vectorial)
2. Extrae entidades mencionadas en esos chunks
3. Hace traversal del grafo desde esas entidades para encontrar chunks relacionados
4. Retorna contexto enriquecido con información relacionada

**Ventajas**:
- Encuentra información relacionada que no está en el chunk original
- Conecta conceptos a través de entidades
- Proporciona contexto más completo para el LLM

**Ejemplo**:
```python
import ungraph

# Búsqueda Graph-Enhanced
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2  # Profundidad de relaciones a explorar
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Contenido: {result.content[:200]}...")
    if result.next_chunk_content:
        print(f"Contexto relacionado: {result.next_chunk_content[:200]}...")
```

**Query Cypher generado**:
```cypher
// 1. Búsqueda vectorial inicial
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $query_vector)
YIELD node as initial_chunk, score as initial_score

// 2. Encontrar entidades mencionadas
OPTIONAL MATCH (initial_chunk)-[:MENTIONS]->(entity:Entity)

// 3. Encontrar otros chunks relacionados a través de entidades
OPTIONAL MATCH path = (entity)<-[:MENTIONS]-(related_chunk:Chunk)
WHERE related_chunk <> initial_chunk

// 4. Retornar contexto enriquecido
RETURN {
    central_chunk: {...},
    related_chunks: [...],
    neighbor_chunks: [...]
} as result
```

---

### 2. Local Retriever

**Requisitos**: `ungraph[gds]` (opcional, funciona sin GDS pero mejor con él)

**Cómo funciona**:
1. Busca chunk central usando full-text search
2. Encuentra comunidad local (chunks relacionados por relaciones del grafo)
3. Agrupa chunks relacionados y genera contexto

**Ventajas**:
- Optimizado para comunidades pequeñas y focalizadas
- Más rápido que Community Summary
- Útil para exploración de conocimiento específico

**Ejemplo**:
```python
import ungraph

results = ungraph.search_with_pattern(
    "neural networks",
    pattern_type="local",
    limit=5,
    community_threshold=3,  # Tamaño mínimo de comunidad
    max_depth=1  # Profundidad de relaciones
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Contenido central: {result.content[:200]}...")
    if result.next_chunk_content:
        print(f"Resumen de comunidad: {result.next_chunk_content[:200]}...")
```

---

### 3. Community Summary Retriever (GDS)

**Requisitos**: `ungraph[gds]` y Neo4j GDS plugin instalado

**Cómo funciona**:
1. Usa algoritmos de detección de comunidades (Louvain, Leiden) de GDS
2. Detecta comunidades de chunks relacionados
3. Genera resúmenes de cada comunidad
4. Busca en los resúmenes en lugar de chunks individuales

**Ventajas**:
- Encuentra temas relacionados aunque estén en diferentes chunks
- Resúmenes capturan el contexto completo de un tema
- Reduce ruido al buscar en resúmenes

**Pre-requisitos**:
Antes de usar este patrón, debes detectar comunidades:

```python
from infrastructure.services.gds_service import GDSService

gds_service = GDSService()
stats = gds_service.detect_communities(
    graph_name="chunk-graph",
    algorithm="louvain",
    write_property="community_id"
)
print(f"Detectadas {stats['community_count']} comunidades")
```

**Ejemplo**:
```python
import ungraph

# Primero detectar comunidades (una vez)
from infrastructure.services.gds_service import GDSService
gds_service = GDSService()
gds_service.detect_communities()

# Luego buscar usando Community Summary
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="community_summary",
    limit=3,
    min_community_size=5
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Contenido: {result.content[:200]}...")
    if result.next_chunk_content:
        print(f"Resumen de comunidad: {result.next_chunk_content[:200]}...")
```

---

## Comparación de Patrones

| Patrón | Requisitos | Velocidad | Precisión | Contexto | Uso |
|--------|-----------|-----------|-----------|----------|-----|
| Basic | Ninguno | ⚡⚡⚡ | ⭐⭐ | ⭐ | Búsquedas simples |
| Metadata Filtering | Ninguno | ⚡⚡⚡ | ⭐⭐⭐ | ⭐ | Filtrar por propiedades |
| Parent-Child | Ninguno | ⚡⚡ | ⭐⭐⭐ | ⭐⭐ | Contexto jerárquico |
| Graph-Enhanced | ungraph[gds] | ⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Búsquedas avanzadas |
| Local | ungraph[gds] | ⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | Comunidades pequeñas |
| Community Summary | ungraph[gds] + GDS | ⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Temas relacionados |

---

## Mejores Prácticas

1. **Empezar simple**: Usa `basic` o `metadata_filtering` primero
2. **Ajustar según necesidad**: Si necesitas más contexto, usa `parent_child`
3. **Para búsquedas avanzadas**: Usa `graph_enhanced` cuando tengas entidades extraídas
4. **Para temas relacionados**: Usa `community_summary` cuando necesites encontrar información distribuida
5. **Performance**: Los patrones avanzados son más lentos pero proporcionan mejor contexto

---

## Requisitos de Índices

**Índices básicos** (siempre requeridos):
- `chunk_content`: Full-text index
- `chunk_embeddings`: Vector index

**Índices adicionales** (para patrones avanzados):
- Nodos `Entity` con relaciones `MENTIONS` (para Graph-Enhanced)
- Propiedad `community_id` en chunks (para Community Summary, requiere GDS)

---

## Referencias

- [Graph-Enhanced Vector Search](https://graphrag.com/reference/graphrag/graph-enhanced-vector-search/)
- [Community Summary Retriever](https://graphrag.com/reference/graphrag/global-community-summary-retriever/)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/)
- [GraphRAG Advanced Patterns](../GRAPHRAG_AVANZADO.md)




