"""
Script para generar y ejecutar queries Cypher que recrean patrones de grafo.

Este script tiene como propósito ejecutar código Cypher para recrear los patrones
que serán necesarios estudiar en la aplicación para verificar que cada patrón está
correctamente generado según GraphRAG patterns. La idea es que se puedan popular
grafos de ejemplo que faciliten el estudio de esto.

Patrones incluidos:
- LEXICAL_GRAPH_PATTERN: Grafo léxico con entidades y relaciones semánticas
- FILE_PAGE_CHUNK_PATTERN: Estructura File-Page-Chunk (patrón actual)
- SEQUENTIAL_CHUNKS_PATTERN: Chunks con relaciones secuenciales
- SIMPLE_CHUNK_PATTERN: Solo chunks sin estructura jerárquica

Referencias:
- GraphRAG Pattern Catalog: https://graphrag.com/reference/
- Documentación Ungraph: docs/concepts/graph-patterns.md
"""

from src.scripts.cypher_test_queries import (
    # Patrones de creación
    FILE_PAGE_CHUNK_CREATE,
    FILE_PAGE_CHUNK_CREATE_RELATIONSHIPS,
    SEQUENTIAL_CHUNKS_CREATE,
    SIMPLE_CHUNK_CREATE,
    LEXICAL_GRAPH_CREATE_ENTITY,
    LEXICAL_GRAPH_CREATE_CHUNK,
    LEXICAL_GRAPH_CREATE_MENTION,
    # Queries de validación
    FILE_PAGE_CHUNK_VALIDATE,
    SEQUENTIAL_CHUNKS_VALIDATE,
    SIMPLE_CHUNK_VALIDATE,
    LEXICAL_GRAPH_VALIDATE
)

# Exportar queries como constantes para uso en validación
LEXICAL_GRAPH_PATTERN = {
    "create_entity": LEXICAL_GRAPH_CREATE_ENTITY,
    "create_chunk": LEXICAL_GRAPH_CREATE_CHUNK,
    "create_mention": LEXICAL_GRAPH_CREATE_MENTION,
    "validate": LEXICAL_GRAPH_VALIDATE
}

FILE_PAGE_CHUNK_PATTERN = {
    "create": FILE_PAGE_CHUNK_CREATE,
    "create_relationships": FILE_PAGE_CHUNK_CREATE_RELATIONSHIPS,
    "validate": FILE_PAGE_CHUNK_VALIDATE
}

SEQUENTIAL_CHUNKS_PATTERN = {
    "create": SEQUENTIAL_CHUNKS_CREATE,
    "validate": SEQUENTIAL_CHUNKS_VALIDATE
}

SIMPLE_CHUNK_PATTERN = {
    "create": SIMPLE_CHUNK_CREATE,
    "validate": SIMPLE_CHUNK_VALIDATE
}
