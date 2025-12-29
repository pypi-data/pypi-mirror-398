# Ejemplos Básicos

Ejemplos simples de uso de Ungraph.

## Ejemplo 1: Ingerir un Documento

```python
import ungraph

# Ingerir documento
chunks = ungraph.ingest_document("mi_documento.md")

print(f"✅ Documento ingerido: {len(chunks)} chunks creados")
```

## Ejemplo 2: Buscar Información

```python
import ungraph

# Buscar
results = ungraph.search("tema de interés", limit=5)

# Mostrar resultados
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print("---")
```

## Ejemplo 3: Búsqueda Híbrida

```python
import ungraph

# Búsqueda híbrida
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.3, 0.7)
)

# Procesar resultados
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content}")
    print("=" * 80)
```

## Ejemplo 4: Obtener Recomendación de Chunking

```python
import ungraph

# Obtener recomendación
recommendation = ungraph.suggest_chunking_strategy("documento.md")

print(f"Estrategia: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explicación: {recommendation.explanation}")

# Usar la recomendación
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
```

## Ejemplo 5: Pipeline Completo

```python
import ungraph

# 1. Configurar
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña"
)

# 2. Obtener recomendación
recommendation = ungraph.suggest_chunking_strategy("documento.md")

# 3. Ingerir
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)

# 4. Buscar
results = ungraph.hybrid_search("tema", limit=5)

# 5. Mostrar resultados
for result in results:
    print(result.content)
```

## Ejemplo 6: Basic Retriever con Lexical Graph

El Basic Retriever es el patrón más básico de GraphRAG. Requiere un Lexical Graph (como `FILE_PAGE_CHUNK`) y funciona buscando similitud directamente en los chunks.

```python
import ungraph

# 1. Crear Lexical Graph (ingerir documento)
print("📄 Ingiriendo documento...")
chunks = ungraph.ingest_document(
    "documento_tecnico.md",
    chunk_size=1000,
    chunk_overlap=200
)
print(f"✅ {len(chunks)} chunks creados en el Lexical Graph\n")

# 2. Buscar usando Basic Retriever
query = "inteligencia artificial y sus aplicaciones"
print(f"🔍 Buscando: '{query}'\n")

results = ungraph.search(query, limit=5)

# 3. Mostrar resultados
print(f"📊 Encontrados {len(results)} resultados:\n")
for i, result in enumerate(results, 1):
    print(f"{'='*80}")
    print(f"Resultado {i}")
    print(f"{'='*80}")
    print(f"Score de similitud: {result.score:.4f}")
    print(f"Chunk ID: {result.chunk_id}")
    print(f"\nContenido:")
    print(f"{result.content[:500]}...")
    print()
```

**Cuándo usar Basic Retriever:**
- ✅ La información está en chunks específicos y bien definidos
- ✅ No necesitas contexto adicional más allá del chunk encontrado
- ✅ Quieres la búsqueda más rápida y simple

**Cuándo NO usar Basic Retriever:**
- ❌ Necesitas contexto completo de una sección → Usa **Parent-Child Retriever**
- ❌ Necesitas filtrar por metadatos → Usa **Metadata Filtering**

## Referencias

- [Guía de Inicio Rápido](../guides/sp-quickstart.md)
- [Guía de Ingesta](../guides/sp-ingestion.md)
- [Guía de Búsqueda](../guides/search.md)
- [Patrones de Búsqueda GraphRAG](../api/sp-search-patterns.md)
