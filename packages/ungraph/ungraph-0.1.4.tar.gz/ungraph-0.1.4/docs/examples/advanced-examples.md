> Documento movido / Document moved

Este documento ahora está disponible en versiones bilingües:

- Español: [sp-advanced-examples.md](sp-advanced-examples.md)
- English: [en-advanced-examples.md](en-advanced-examples.md)

Por favor actualiza tus enlaces y marcadores a una de las versiones anteriores.

Please update your links/bookmarks to one of the above versions.

## Ejemplo 1: Ingerir Múltiples Documentos

```python
import ungraph
from pathlib import Path

# Lista de archivos
archivos = ["doc1.md", "doc2.txt", "doc3.docx"]

# Ingerir todos
for archivo in archivos:
    try:
        chunks = ungraph.ingest_document(archivo)
        print(f"✅ {archivo}: {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error con {archivo}: {e}")
```

## Ejemplo 2: Reconstruir Contexto Completo

```python
import ungraph

# Buscar
results = ungraph.hybrid_search("tema", limit=3)

# Reconstruir contexto completo para cada resultado
for result in results:
    contexto_completo = ""
    
    if result.previous_chunk_content:
        contexto_completo += f"[Anterior]\n{result.previous_chunk_content}\n\n"
    
    contexto_completo += f"[Principal]\n{result.content}\n\n"
    
    if result.next_chunk_content:
        contexto_completo += f"[Siguiente]\n{result.next_chunk_content}"
    
    print(contexto_completo)
    print("=" * 80)
```

## Ejemplo 3: Crear Patrón Personalizado

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition
)
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService

# Crear patrón simple
chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={"chunk_id": str, "content": str},
    indexes=["chunk_id"]
)

simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Solo chunks",
    node_definitions=[chunk_node],
    relationship_definitions=[]
)

# Validar
service = Neo4jPatternService()
is_valid = service.validate_pattern(simple_pattern)
print(f"Patrón válido: {is_valid}")

# Generar query Cypher
cypher = service.generate_cypher(simple_pattern, "create")
print(f"Query generado:\n{cypher}")
```

## Ejemplo 4: Análisis de Resultados

```python
import ungraph
from collections import Counter

# Buscar
results = ungraph.hybrid_search("machine learning", limit=20)

# Analizar resultados
print(f"Total de resultados: {len(results)}")
print(f"Score promedio: {sum(r.score for r in results) / len(results):.3f}")
print(f"Score máximo: {max(r.score for r in results):.3f}")
print(f"Score mínimo: {min(r.score for r in results):.3f}")

# Contar chunks con contexto
con_contexto = sum(1 for r in results if r.previous_chunk_content or r.next_chunk_content)
print(f"Resultados con contexto: {con_contexto}/{len(results)}")
```

## Ejemplo 5: Comparar Estrategias de Búsqueda

```python
import ungraph

query = "deep learning"

# Búsqueda por texto
text_results = ungraph.search(query, limit=5)

# Búsqueda híbrida con diferentes pesos
hybrid_1 = ungraph.hybrid_search(query, limit=5, weights=(0.7, 0.3))  # Más texto
hybrid_2 = ungraph.hybrid_search(query, limit=5, weights=(0.3, 0.7))  # Más vectorial

print("Búsqueda por texto:")
for r in text_results[:3]:
    print(f"  Score: {r.score:.3f}")

print("\nHíbrida (más texto):")
for r in hybrid_1[:3]:
    print(f"  Score: {r.score:.3f}")

print("\nHíbrida (más vectorial):")
for r in hybrid_2[:3]:
    print(f"  Score: {r.score:.3f}")
```

## Ejemplo 6: Parent-Child Retriever

El Parent-Child Retriever mejora la calidad de los resultados cuando necesitas contexto completo. Busca en chunks pequeños (hijos) y recupera el chunk padre (contexto completo).

```python
import ungraph
from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

# 1. Crear estructura padre-hijo (ingerir documento)
print("📄 Ingiriendo documento largo...")
chunks = ungraph.ingest_document(
    "documento_tecnico.md",
    chunk_size=500,  # Chunks pequeños para mejor matching
    chunk_overlap=100
)
print(f"✅ {len(chunks)} chunks creados\n")

# 2. Buscar usando Parent-Child Retriever
query = "arquitectura de redes neuronales profundas"
print(f"🔍 Buscando: '{query}'\n")

search_service = Neo4jSearchService()
results = search_service.search_with_pattern(
    query_text=query,
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=3
)

# 3. Mostrar resultados con contexto completo
print(f"📊 Encontrados {len(results)} resultados:\n")
for i, result in enumerate(results, 1):
    print(f"{'='*80}")
    print(f"Resultado {i}")
    print(f"{'='*80}")
    print(f"📄 Page (Padre) - Score: {result.parent_score:.4f}")
    print(f"\n{result.parent_content[:400]}...")
    print(f"\n📦 Chunks relacionados: {len(result.children)}")
    
    # Mostrar primeros 3 hijos
    for j, child in enumerate(result.children[:3], 1):
        print(f"\n  Chunk {j}:")
        print(f"  {child['content'][:250]}...")
    
    print(f"\n{'='*80}\n")

search_service.close()
```

**Cuándo usar Parent-Child Retriever:**
- ✅ Muchos temas en un chunk afectan negativamente la calidad de los vectores
- ✅ Necesitas contexto completo de una sección para generar respuestas
- ✅ Los chunks pequeños tienen mejor representación vectorial pero falta contexto

## Ejemplo 7: Patrones de Búsqueda GraphRAG (Metadata Filtering)

Búsqueda con filtros por metadatos. Útil para buscar solo en documentos específicos.

```python
import ungraph

# Buscar solo en un archivo específico
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md"
    },
    limit=10
)

# Buscar en una página específica
results = ungraph.search_with_pattern(
    "deep learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md",
        "page_number": 1
    },
    limit=5
)

# Procesar resultados
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print("---")
```

## Ejemplo 8: Comparación de Patrones de Búsqueda

```python
import ungraph

query = "computación cuántica"

# Búsqueda normal (sin filtros)
results_normal = ungraph.search(query, limit=5)
print(f"Búsqueda normal: {len(results_normal)} resultados")

# Búsqueda con filtro de metadatos
results_filtered = ungraph.search_with_pattern(
    query,
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "quantum_computing.md"},
    limit=5
)
print(f"Búsqueda filtrada: {len(results_filtered)} resultados")

# Comparación: Basic vs Parent-Child
print("\n--- Basic Retriever ---")
basic_results = ungraph.search(query, limit=3)
for r in basic_results:
    print(f"Score: {r.score:.3f} - Solo chunk")

print("\n--- Parent-Child Retriever ---")
search_service = Neo4jSearchService()
parent_child_results = search_service.search_with_pattern(
    query,
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    limit=3
)
for r in parent_child_results:
    print(f"Score: {r.parent_score:.3f} - Page + {len(r.children)} chunks hijos")
search_service.close()
```

## Referencias

- [Guía de Patrones Personalizados](../guides/sp-custom-patterns.md)
- [Patrones de Búsqueda GraphRAG](../api/sp-search-patterns.md)
- [Lexical Graphs](../concepts/lexical-graphs.md)




