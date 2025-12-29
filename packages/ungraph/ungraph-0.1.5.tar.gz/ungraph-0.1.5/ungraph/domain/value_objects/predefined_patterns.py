"""
Patrones de grafo predefinidos.

Estos patrones reflejan estructuras comunes de grafos de conocimiento.
El patrón FILE_PAGE_CHUNK es el patrón actual usado en el sistema.

Referencias:
- Código actual: src/utils/graph_operations.py::extract_document_structure
"""

from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition
)


# Patrón actual (FILE-PAGE-CHUNK)
# Refleja exactamente la estructura implementada en extract_document_structure
FILE_PAGE_CHUNK_PATTERN = GraphPattern(
    name="FILE_PAGE_CHUNK",
    description="Patrón básico: File contiene Pages, Pages contienen Chunks. Chunks tienen relaciones NEXT_CHUNK entre consecutivos.",
    node_definitions=[
        NodeDefinition(
            label="File",
            required_properties={"filename": str},
            optional_properties={"createdAt": int},
            indexes=["filename"]
        ),
        NodeDefinition(
            label="Page",
            required_properties={
                "filename": str,
                "page_number": int
            },
            optional_properties={},
            indexes=["filename", "page_number"]
        ),
        NodeDefinition(
            label="Chunk",
            required_properties={
                "chunk_id": str,
                "page_content": str,
                "embeddings": list,
                "embeddings_dimensions": int
            },
            optional_properties={
                "is_unitary": bool,
                "chunk_id_consecutive": int,
                "embedding_encoder_info": str
            },
            indexes=["chunk_id", "chunk_id_consecutive"]
        )
    ],
    relationship_definitions=[
        RelationshipDefinition(
            from_node="File",
            to_node="Page",
            relationship_type="CONTAINS",
            direction="OUTGOING"
        ),
        RelationshipDefinition(
            from_node="Page",
            to_node="Chunk",
            relationship_type="HAS_CHUNK",
            direction="OUTGOING"
        ),
        RelationshipDefinition(
            from_node="Chunk",
            to_node="Chunk",
            relationship_type="NEXT_CHUNK",
            direction="OUTGOING"
        )
    ],
    search_patterns=["basic", "hybrid"]
)







