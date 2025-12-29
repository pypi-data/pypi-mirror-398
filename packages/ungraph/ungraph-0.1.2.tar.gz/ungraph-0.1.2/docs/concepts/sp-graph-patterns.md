# Patrones de Grafo

## Introducción

Los patrones de grafo permiten definir estructuras de conocimiento de manera declarativa y reutilizable. En lugar de tener código hardcodeado para cada estructura, puedes definir patrones que describen cómo deben organizarse los nodos y relaciones en el grafo.

## Lexical Graphs vs Knowledge Graphs

Antes de profundizar en los patrones, es importante entender dos conceptos fundamentales:

- **Lexical Graph (Grafo Léxico)**: Estructura que organiza texto y captura relaciones lingüísticas. Se enfoca en la estructura del lenguaje y facilita la búsqueda semántica. El patrón `FILE_PAGE_CHUNK` es un ejemplo de Lexical Graph.

- **Knowledge Graph (Grafo de Conocimiento)**: Estructura que representa conocimiento factual y relaciones entre entidades del dominio. Se enfoca en hechos verificables y esquemas estructurados.

**En Ungraph**: La mayoría de los patrones implementados son **Lexical Graphs** porque organizan texto no estructurado para búsqueda y recuperación. Ver [Lexical Graphs](./sp-lexical-graphs.md) para más detalles.

## Conceptos Básicos

### NodeDefinition

Define un tipo de nodo en el patrón:

```python
from ungraph.domain.value_objects.graph_pattern import NodeDefinition

file_node = NodeDefinition(
    label="File",
    required_properties={"filename": str},
    optional_properties={"createdAt": int},
    indexes=["filename"]
)
```

**Características:**
- `label`: Label del nodo en Neo4j (debe empezar con mayúscula)
- `required_properties`: Propiedades obligatorias {nombre: tipo}
- `optional_properties`: Propiedades opcionales {nombre: tipo}
- `indexes`: Lista de propiedades a indexar para búsquedas rápidas

### RelationshipDefinition

Define una relación entre nodos:

```python
from ungraph.domain.value_objects.graph_pattern import RelationshipDefinition

contains_rel = RelationshipDefinition(
    from_node="File",
    to_node="Page",
    relationship_type="CONTAINS",
    direction="OUTGOING"
)
```

**Características:**
- `from_node`: Label del nodo origen
- `to_node`: Label del nodo destino
- `relationship_type`: Tipo de relación (debe empezar con mayúscula)
- `direction`: "OUTGOING" o "INCOMING"
- `properties`: Propiedades opcionales de la relación

### GraphPattern

Un patrón completo que combina nodos y relaciones:

```python
from ungraph.domain.value_objects.graph_pattern import GraphPattern

pattern = GraphPattern(
    name="FILE_PAGE_CHUNK",
    description="File contiene Pages, Pages contienen Chunks",
    node_definitions=[file_node, page_node, chunk_node],
    relationship_definitions=[contains_rel, has_chunk_rel]
)
```

## Patrón Predefinido: FILE_PAGE_CHUNK

Este es el patrón por defecto usado en Ungraph. Es un **Lexical Graph** que organiza texto no estructurado para búsqueda semántica.

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                    Chunk -[:NEXT_CHUNK]-> Chunk
```

### ¿Por qué es un Lexical Graph?

Este patrón es un Lexical Graph porque:
- **Organiza texto estructuralmente**: Divide documentos en chunks relacionados
- **Captura relaciones lingüísticas**: Los chunks están conectados por relaciones que reflejan la estructura del texto
- **Facilita búsqueda semántica**: Los embeddings en cada chunk permiten búsqueda por similitud semántica
- **Soporta patrones GraphRAG**: Es compatible con Basic Retriever y Parent-Child Retriever

### Estructura

- **File**: Representa un archivo físico
  - Propiedades: `filename`, `createdAt` (opcional)
- **Page**: Representa una página dentro del archivo
  - Propiedades: `filename`, `page_number`
- **Chunk**: Representa un fragmento de texto con embeddings
  - Propiedades: `chunk_id`, `page_content`, `embeddings`, `embeddings_dimensions`
  - Opcionales: `is_unitary`, `chunk_id_consecutive`, `embedding_encoder_info`

### Relaciones

- `File -[:CONTAINS]-> Page`: Un archivo contiene páginas
- `Page -[:HAS_CHUNK]-> Chunk`: Una página tiene chunks
- `Chunk -[:NEXT_CHUNK]-> Chunk`: Chunks consecutivos están relacionados (permite navegación secuencial)

### Uso en GraphRAG

Este patrón es compatible con:
- ✅ **Basic Retriever**: Búsqueda vectorial directa en chunks
- ✅ **Parent-Child Retriever**: Puede evolucionar a estructura padre-hijo
- ✅ **Metadata Filtering**: Filtrado por propiedades de File/Page

Ver [Lexical Graphs](./sp-lexical-graphs.md) para más información sobre cómo funciona este patrón en GraphRAG.

## Crear Patrones Personalizados

### Ejemplo: Patrón Simple (Solo Chunks)

```python
from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition
)

simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Solo chunks, sin estructura File-Page",
    node_definitions=[
        NodeDefinition(
            label="Chunk",
            required_properties={
                "chunk_id": str,
                "content": str
            },
            indexes=["chunk_id"]
        )
    ],
    relationship_definitions=[]
)
```

### Ejemplo: Patrón con Relaciones Personalizadas

```python
entity_node = NodeDefinition(
    label="Entity",
    required_properties={"name": str, "type": str},
    indexes=["name"]
)

chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={"chunk_id": str, "content": str},
    indexes=["chunk_id"]
)

# Relación: Chunk menciona Entity
mentions_rel = RelationshipDefinition(
    from_node="Chunk",
    to_node="Entity",
    relationship_type="MENTIONS",
    properties={"count": int},  # Propiedad en la relación
    direction="OUTGOING"
)

lexical_pattern = GraphPattern(
    name="LEXICAL_GRAPH",
    description="Grafo léxico con entidades y chunks",
    node_definitions=[entity_node, chunk_node],
    relationship_definitions=[mentions_rel]
)
```

## Validaciones

Los patrones se validan automáticamente:

1. **Labels y Relationship Types**: Deben empezar con mayúscula y contener solo letras, números y underscores
2. **Propiedades**: Los nombres deben ser válidos identificadores Python
3. **Relaciones**: Deben referenciar nodos que existen en el patrón
4. **Índices**: Solo pueden indexar propiedades que existen

## Uso de Patrones

### En Ingesta

```python
import ungraph
from ungraph.domain.value_objects.predefined_patterns import FILE_PAGE_CHUNK_PATTERN

# Usar patrón predefinido
chunks = ungraph.ingest_document(
    "documento.md",
    pattern=FILE_PAGE_CHUNK_PATTERN
)

# O usar patrón personalizado
chunks = ungraph.ingest_document(
    "documento.md",
    pattern=simple_pattern
)
```

### Validar un Patrón

```python
from ungraph.infrastructure.services.neo4j_pattern_service import Neo4jPatternService

service = Neo4jPatternService()
is_valid = service.validate_pattern(my_pattern)

if is_valid:
    print("Patrón válido")
else:
    print("Patrón inválido")
```

## Referencias

- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [Neo4j Cypher Manual - Patterns](https://neo4j.com/docs/cypher-manual/current/patterns/)
- [Clean Architecture - Value Objects](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
