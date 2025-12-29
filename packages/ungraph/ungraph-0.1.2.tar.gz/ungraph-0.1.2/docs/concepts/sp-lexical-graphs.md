# Lexical Graphs (Grafos Léxicos)

## ¿Qué es un Lexical Graph según GraphRAG?

Un **Lexical Graph** (según la definición de GraphRAG) es una estructura de datos que organiza **texto en chunks** con relaciones `PART_OF`. Se usa para búsqueda semántica básica en sistemas GraphRAG.

**Importante**: No debe confundirse con "grafos léxicos lingüísticos" que representan relaciones entre palabras (sinónimos, antónimos, etc.). Un Lexical Graph de GraphRAG es una estructura de chunks de texto, no de palabras individuales.

### Características Clave

- **Enfoque**: Organización estructural de texto en chunks
- **Relaciones**: `PART_OF` (o equivalentes como `CONTAINS`, `HAS_CHUNK`) entre chunks y documentos
- **Propósito**: Facilitar búsqueda semántica usando embeddings y estructura del texto
- **Uso**: Patrones básicos de GraphRAG como Basic Retriever y Parent-Child Retriever

### Estructura Típica

```
Document -[:PART_OF]-> Chunk
Chunk -[:NEXT_CHUNK]-> Chunk  (para mantener secuencia)
```

## Lexical Graph vs Knowledge Graph

Es importante diferenciar entre estos dos conceptos:

| Aspecto | Lexical Graph (GraphRAG) | Knowledge Graph |
|---------|-------------------------|-----------------|
| **Enfoque** | Estructura de chunks de texto | Conocimiento factual estructurado |
| **Relaciones** | Estructurales (PART_OF, NEXT_CHUNK) | Semánticas del dominio (AUTOR_DE, PARTE_DE, etc.) |
| **Ejemplo** | Document → Chunk → Chunk (secuencia) | "Einstein" → "es autor de" → "Relatividad" |
| **Uso en GraphRAG** | Búsqueda básica (Basic Retriever) | Búsqueda avanzada (Graph-Enhanced Vector Search) |

### Ejemplo Comparativo

**Lexical Graph (GraphRAG)**:
```
File:documento.md -[:CONTAINS]-> Page:1 -[:HAS_CHUNK]-> Chunk:1
Chunk:1 -[:NEXT_CHUNK]-> Chunk:2
Chunk:2 contiene texto sobre "machine learning"
```

**Knowledge Graph (Domain Graph)**:
```
Persona:Einstein -[:AUTOR_DE]-> Paper:Relatividad
Paper:Relatividad -[:CITA]-> Paper:Mecánica_Cuántica
```

**Diferencia clave**: El Lexical Graph organiza el texto estructuralmente (chunks), mientras que el Knowledge Graph representa conocimiento factual (entidades y relaciones del dominio).

## Lexical Graphs en Ungraph

### El Patrón FILE_PAGE_CHUNK es un Lexical Graph

En Ungraph, el patrón `FILE_PAGE_CHUNK` implementa un **Lexical Graph (según GraphRAG)** porque:

1. **Organiza texto estructuralmente**: Divide documentos en chunks relacionados
2. **Captura relaciones estructurales**: Los chunks están conectados por relaciones que reflejan la estructura del texto (CONTAINS, HAS_CHUNK, NEXT_CHUNK)
3. **Facilita búsqueda semántica**: Los embeddings en cada chunk permiten búsqueda por similitud semántica

### Estructura del Lexical Graph en Ungraph

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                              Chunk -[:NEXT_CHUNK]-> Chunk
```

**Características**:
- **File**: Representa el documento fuente
- **Page**: Representa páginas/secciones del documento
- **Chunk**: Contiene texto y embeddings (representación semántica)
- **Relaciones**: Estructuran el texto de manera jerárquica y secuencial

### Propiedades de los Chunks (Nodos del Lexical Graph)

Cada nodo `Chunk` contiene:
- `page_content`: El texto del chunk
- `embeddings`: Representación vectorial del texto (similitud semántica)
- `chunk_id`: Identificador único
- `chunk_id_consecutive`: Orden secuencial

Estas propiedades permiten:
- **Búsqueda vectorial**: Usando embeddings para encontrar chunks semánticamente similares
- **Búsqueda de texto**: Usando `page_content` para búsqueda full-text
- **Navegación secuencial**: Usando `NEXT_CHUNK` para recorrer el documento

## Uso de Lexical Graphs en GraphRAG

### Patrón: Basic Retriever

El **Basic Retriever** requiere un Lexical Graph porque:

1. **Vectoriza la pregunta**: Usa el mismo modelo de embeddings que los chunks
2. **Busca similitud**: Encuentra los k chunks más similares usando embeddings
3. **Retorna texto**: Devuelve el `page_content` de los chunks encontrados

**Ejemplo**:
```python
# La pregunta se vectoriza
query_embedding = embedding_service.generate_embedding("¿Qué es machine learning?")

# Se busca similitud en los embeddings de los chunks
results = search_service.vector_search(query_embedding, limit=5)

# Se retornan los chunks más similares
for result in results:
    print(result.content)  # page_content del chunk
```

### Patrón: Parent-Child Retriever

El **Parent-Child Retriever** es una evolución del Lexical Graph:

- **Chunks pequeños (hijos)**: Mejor representación vectorial (menos ruido)
- **Chunks grandes (padres)**: Contexto completo para generación

**Estructura**:
```
Page (padre) -[:HAS_CHILD]-> Chunk (hijo)
Chunk (hijo) -[:PART_OF]-> Page (padre)
```

**Flujo**:
1. Busca en chunks pequeños (mejor matching vectorial)
2. Recupera el chunk padre (contexto completo)
3. Usa el contexto completo para generar respuesta

## Cuándo Usar Lexical Graphs

### ✅ Usa Lexical Graph cuando:

- Necesitas organizar texto no estructurado
- Quieres búsqueda semántica en documentos
- Los documentos tienen estructura jerárquica (páginas, secciones)
- Necesitas mantener el orden secuencial del texto
- Quieres implementar patrones básicos de GraphRAG (Basic Retriever, Parent-Child)

### ❌ No uses Lexical Graph cuando:

- Necesitas representar conocimiento factual estructurado
- Las relaciones son entre entidades del dominio (personas, lugares, conceptos)
- Necesitas un esquema fijo de conocimiento
- Quieres representar hechos verificables

En estos casos, considera usar un **Knowledge Graph** (Domain Graph).

## Ejemplo Práctico

### Crear un Lexical Graph con Ungraph

```python
import ungraph

# Ingerir documento (crea Lexical Graph automáticamente)
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=1000,
    chunk_overlap=200
)

# El grafo creado es un Lexical Graph:
# File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
#                              Chunk -[:NEXT_CHUNK]-> Chunk

# Buscar usando Basic Retriever (requiere Lexical Graph)
results = ungraph.search("machine learning", limit=5)

# Cada resultado es un chunk del Lexical Graph
for result in results:
    print(f"Chunk ID: {result.chunk_id}")
    print(f"Contenido: {result.content[:200]}...")
    print(f"Score: {result.score}")
```

### Visualizar el Lexical Graph

```cypher
// Ver estructura del Lexical Graph
MATCH path = (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN path
LIMIT 50

// Ver relaciones secuenciales
MATCH path = (c1:Chunk)-[:NEXT_CHUNK]->(c2:Chunk)
RETURN path
LIMIT 20
```

## Referencias

- [GraphRAG - Lexical Graphs](https://graphrag.com/reference/knowledge-graph/lexical-graph/)
- [Patrones de Grafo en Ungraph](./sp-graph-patterns.md)
- [Patrones de Búsqueda GraphRAG](../api/sp-search-patterns.md)
- [Grafo Léxico - Conceptos](../../src/notebooks/Grafo%20Léxico.md)
