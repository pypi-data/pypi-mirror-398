# Guía de Patrones Personalizados

Esta guía explica cómo crear y usar patrones de grafo personalizados en Ungraph.

## ¿Qué son los Patrones?

Los patrones definen la estructura del grafo de conocimiento. El patrón por defecto es `FILE_PAGE_CHUNK`, pero puedes crear patrones personalizados para diferentes necesidades.

## Crear un Patrón Simple

### Ejemplo: Solo Chunks

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition
)

# Definir nodo Chunk
chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={
        "chunk_id": str,
        "content": str
    },
    indexes=["chunk_id"]
)

# Crear patrón
simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Solo chunks, sin estructura File-Page",
    node_definitions=[chunk_node],
    relationship_definitions=[]
)
```

## Crear un Patrón con Relaciones

### Ejemplo: Entidades y Chunks

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition
)

# Nodo Entity
entity_node = NodeDefinition(
    label="Entity",
    required_properties={
        "name": str,
        "type": str
    },
    optional_properties={
        "description": str
    },
    indexes=["name", "type"]
)

# Nodo Chunk
chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={
        "chunk_id": str,
        "content": str
    },
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

# Crear patrón
lexical_pattern = GraphPattern(
    name="LEXICAL_GRAPH",
    description="Grafo léxico con entidades y chunks",
    node_definitions=[entity_node, chunk_node],
    relationship_definitions=[mentions_rel]
)
```

## Validar un Patrón

Antes de usar un patrón, valídalo:

```python
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService

service = Neo4jPatternService()
is_valid = service.validate_pattern(my_pattern)

if is_valid:
    print("✅ Patrón válido")
else:
    print("❌ Patrón inválido")
```

## Generar Query Cypher

Puedes ver el query Cypher que se generaría para tu patrón:

```python
service = Neo4jPatternService()
cypher_query = service.generate_cypher(my_pattern, "create")

print("Query Cypher generado:")
print(cypher_query)
```

## Usar un Patrón Personalizado

**Nota:** La integración con `ingest_document()` está en desarrollo (Fase 2). Por ahora puedes usar el patrón directamente con `PatternService`:

```python
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService

service = Neo4jPatternService()

# Datos para el patrón
data = {
    "chunk_id": "chunk_1",
    "content": "Contenido del chunk"
}

# Aplicar patrón (requiere Neo4j configurado)
# service.apply_pattern(simple_pattern, data)
```

## Reglas de Validación

### Labels de Nodos

- Deben empezar con mayúscula
- Solo letras, números y underscores
- Ejemplos válidos: `File`, `Page`, `Chunk`, `Entity`
- Ejemplos inválidos: `file`, `File-Name`, `file_name`

### Relationship Types

- Deben empezar con mayúscula
- Solo letras mayúsculas, números y underscores
- Ejemplos válidos: `CONTAINS`, `HAS_CHUNK`, `NEXT_CHUNK`
- Ejemplos inválidos: `contains`, `has-chunk`

### Propiedades

- Nombres deben ser identificadores Python válidos
- Tipos deben ser tipos Python (`str`, `int`, `list`, etc.)

## Ejemplos Completos

### Patrón: Documento → Sección → Párrafo

```python
document_node = NodeDefinition(
    label="Document",
    required_properties={"doc_id": str, "title": str},
    indexes=["doc_id"]
)

section_node = NodeDefinition(
    label="Section",
    required_properties={"section_id": str, "title": str},
    indexes=["section_id"]
)

paragraph_node = NodeDefinition(
    label="Paragraph",
    required_properties={"para_id": str, "content": str},
    indexes=["para_id"]
)

# Relaciones
has_section = RelationshipDefinition(
    from_node="Document",
    to_node="Section",
    relationship_type="HAS_SECTION"
)

has_paragraph = RelationshipDefinition(
    from_node="Section",
    to_node="Paragraph",
    relationship_type="HAS_PARAGRAPH"
)

document_pattern = GraphPattern(
    name="DOCUMENT_SECTION_PARAGRAPH",
    description="Documento contiene secciones, secciones contienen párrafos",
    node_definitions=[document_node, section_node, paragraph_node],
    relationship_definitions=[has_section, has_paragraph]
)
```

## Referencias

- [Documentación de Patrones](../concepts/sp-graph-patterns.md)
- [Plan de Patrones](../../_PLAN_PATRONES_GRAFO.md)
- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
