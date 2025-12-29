"""
Queries Cypher para recrear y validar patrones de grafo.

Este módulo contiene queries Cypher que recrean los diferentes patrones
mencionados en generators.py para facilitar el estudio y validación.

Patrones incluidos:
- LEXICAL_GRAPH_PATTERN: Grafo léxico con entidades y relaciones semánticas
- FILE_PAGE_CHUNK_PATTERN: Estructura File-Page-Chunk (patrón actual)
- SEQUENTIAL_CHUNKS_PATTERN: Chunks con relaciones secuenciales
- SIMPLE_CHUNK_PATTERN: Solo chunks sin estructura jerárquica
"""

# ============================================================================
# PATRÓN 1: FILE_PAGE_CHUNK_PATTERN
# ============================================================================
# Patrón actual implementado en extract_document_structure
# Estructura: File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
# Compatible con GraphRAG: Basic Retriever, Parent-Child Retriever

FILE_PAGE_CHUNK_CREATE = """
// Crear estructura FILE_PAGE_CHUNK completa
MERGE (f:File {filename: $filename})
ON CREATE SET f.createdAt = timestamp()

MERGE (p:Page {filename: $filename, page_number: toInteger($page_number)})

MERGE (c:Chunk {chunk_id: $chunk_id})
ON CREATE SET c.page_content = $page_content,
              c.is_unitary = $is_unitary,
              c.embeddings = $embeddings,
              c.embeddings_dimensions = toInteger($embeddings_dimensions),
              c.embedding_encoder_info = $embedding_encoder_info,
              c.chunk_id_consecutive = toInteger($chunk_id_consecutive)

MERGE (f)-[:CONTAINS]->(p)
MERGE (p)-[:HAS_CHUNK]->(c)
"""

FILE_PAGE_CHUNK_CREATE_RELATIONSHIPS = """
// Crear relaciones NEXT_CHUNK entre chunks consecutivos
MATCH (c1:Chunk), (c2:Chunk)
WHERE c1.chunk_id_consecutive + 1 = c2.chunk_id_consecutive
MERGE (c1)-[:NEXT_CHUNK]->(c2)
"""

FILE_PAGE_CHUNK_VALIDATE = """
// Validar estructura FILE_PAGE_CHUNK
MATCH (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
WHERE f.filename = $filename
RETURN f.filename as file,
       count(DISTINCT p) as pages,
       count(DISTINCT c) as chunks,
       collect(DISTINCT p.page_number) as page_numbers
ORDER BY p.page_number
"""

# ============================================================================
# PATRÓN 2: SEQUENTIAL_CHUNKS_PATTERN
# ============================================================================
# Patrón que enfatiza relaciones secuenciales entre chunks
# Útil para navegación secuencial y contexto continuo

SEQUENTIAL_CHUNKS_CREATE = """
// Crear chunks con relaciones secuenciales explícitas
MERGE (c1:Chunk {chunk_id: $chunk_id_1})
ON CREATE SET c1.page_content = $content_1,
              c1.chunk_id_consecutive = toInteger($consecutive_1),
              c1.embeddings = $embeddings_1

MERGE (c2:Chunk {chunk_id: $chunk_id_2})
ON CREATE SET c2.page_content = $content_2,
              c2.chunk_id_consecutive = toInteger($consecutive_2),
              c2.embeddings = $embeddings_2

MERGE (c1)-[:NEXT_CHUNK]->(c2)
"""

SEQUENTIAL_CHUNKS_QUERY = """
// Consultar secuencia de chunks
MATCH path = (start:Chunk)-[:NEXT_CHUNK*]->(end:Chunk)
WHERE start.chunk_id_consecutive = $start_consecutive
  AND end.chunk_id_consecutive = $end_consecutive
RETURN [n IN nodes(path) | {
    chunk_id: n.chunk_id,
    consecutive: n.chunk_id_consecutive,
    content: n.page_content
}] as sequence
ORDER BY n.chunk_id_consecutive
"""

SEQUENTIAL_CHUNKS_VALIDATE = """
// Validar integridad de secuencia
MATCH (c:Chunk)
WHERE c.chunk_id_consecutive IS NOT NULL
WITH c.chunk_id_consecutive as consecutive
ORDER BY consecutive
WITH collect(consecutive) as consecutives
RETURN 
    size(consecutives) as total_chunks,
    consecutives[0] as first,
    consecutives[-1] as last,
    all(i IN range(0, size(consecutives)-2) 
        WHERE consecutives[i] + 1 = consecutives[i+1]) as is_sequential
"""

# ============================================================================
# PATRÓN 3: SIMPLE_CHUNK_PATTERN
# ============================================================================
# Patrón minimalista: solo chunks sin estructura File-Page
# Útil para casos simples donde no se necesita jerarquía

SIMPLE_CHUNK_CREATE = """
// Crear chunk simple sin estructura File-Page
MERGE (c:Chunk {chunk_id: $chunk_id})
ON CREATE SET c.page_content = $page_content,
              c.embeddings = $embeddings,
              c.embeddings_dimensions = toInteger($embeddings_dimensions),
              c.chunk_id_consecutive = toInteger($chunk_id_consecutive)
"""

SIMPLE_CHUNK_QUERY = """
// Consultar chunks simples
MATCH (c:Chunk)
WHERE NOT EXISTS((c)<-[:HAS_CHUNK]-())
  AND NOT EXISTS((c)<-[:CONTAINS]-())
RETURN c.chunk_id as chunk_id,
       c.page_content as content,
       c.chunk_id_consecutive as consecutive
ORDER BY c.chunk_id_consecutive
LIMIT $limit
"""

SIMPLE_CHUNK_VALIDATE = """
// Validar que chunks no tienen relaciones File-Page
MATCH (c:Chunk)
OPTIONAL MATCH (c)<-[:HAS_CHUNK]-(p:Page)
OPTIONAL MATCH (c)<-[:CONTAINS]-(f:File)
RETURN count(c) as total_chunks,
       count(p) as chunks_with_page,
       count(f) as chunks_with_file,
       count(c) - count(p) as simple_chunks
"""

# ============================================================================
# PATRÓN 4: LEXICAL_GRAPH_PATTERN
# ============================================================================
# Grafo léxico con entidades y relaciones semánticas
# Estructura: Chunk -[:MENTIONS]-> Entity
# Compatible con GraphRAG: Basic Retriever, Metadata Filtering

LEXICAL_GRAPH_CREATE_ENTITY = """
// Crear entidad en grafo léxico
MERGE (e:Entity {name: $entity_name, type: $entity_type})
ON CREATE SET e.createdAt = timestamp()
"""

LEXICAL_GRAPH_CREATE_CHUNK = """
// Crear chunk en grafo léxico
MERGE (c:Chunk {chunk_id: $chunk_id})
ON CREATE SET c.page_content = $page_content,
              c.embeddings = $embeddings,
              c.embeddings_dimensions = toInteger($embeddings_dimensions)
"""

LEXICAL_GRAPH_CREATE_MENTION = """
// Crear relación MENTIONS entre Chunk y Entity
MATCH (c:Chunk {chunk_id: $chunk_id})
MATCH (e:Entity {name: $entity_name})
MERGE (c)-[r:MENTIONS]->(e)
ON CREATE SET r.count = 1
ON MATCH SET r.count = r.count + 1
"""

LEXICAL_GRAPH_QUERY = """
// Consultar grafo léxico: chunks que mencionan entidades
MATCH (c:Chunk)-[r:MENTIONS]->(e:Entity)
WHERE e.type = $entity_type
RETURN c.chunk_id as chunk_id,
       c.page_content as content,
       e.name as entity_name,
       e.type as entity_type,
       r.count as mention_count
ORDER BY r.count DESC
LIMIT $limit
"""

LEXICAL_GRAPH_VALIDATE = """
// Validar estructura de grafo léxico
MATCH (c:Chunk)-[r:MENTIONS]->(e:Entity)
RETURN count(DISTINCT c) as chunks_with_mentions,
       count(DISTINCT e) as total_entities,
       count(r) as total_mentions,
       avg(r.count) as avg_mentions_per_entity
"""

# ============================================================================
# QUERIES DE BÚSQUEDA GRAPHRAG
# ============================================================================

# Basic Retriever (ya implementado en graphrag_search_patterns.py)
BASIC_RETRIEVER_QUERY = """
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
RETURN node.page_content as content,
       score,
       node.chunk_id as chunk_id,
       node.chunk_id_consecutive as chunk_id_consecutive
ORDER BY score DESC
LIMIT $limit
"""

# Metadata Filtering (ya implementado)
METADATA_FILTERING_QUERY = """
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
WHERE node.filename = $filename AND node.page_number = $page_number
RETURN node.page_content as content,
       score,
       node.chunk_id as chunk_id,
       node.chunk_id_consecutive as chunk_id_consecutive
ORDER BY score DESC
LIMIT $limit
"""

# Parent-Child Retriever (ya implementado)
PARENT_CHILD_RETRIEVER_QUERY = """
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as parent_node, score as parent_score

OPTIONAL MATCH (parent_node:Page)-[:HAS_CHUNK]->(child_node:Chunk)

WITH parent_node, parent_score, collect(DISTINCT {
    content: child_node.page_content,
    chunk_id: child_node.chunk_id
}) as children

RETURN {
    parent_content: parent_node.page_content,
    parent_score: parent_score,
    parent_chunk_id: parent_node.chunk_id,
    children: children
} as result,
parent_score
ORDER BY parent_score DESC
LIMIT $limit
"""

# Hybrid Search (ya implementado en graph_rags.py)
HYBRID_SEARCH_QUERY = """
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as text_node, score as text_score

CALL {
    WITH text_node
    CALL db.index.vector.queryNodes('chunk_embeddings', toInteger($top_k), $query_vector)
    YIELD node as vec_node, score as vec_score
    WHERE text_node = vec_node
    RETURN vec_node, vec_score
}

WITH text_node as node, text_score, vec_score,
     (text_score * $text_weight + vec_score * $vector_weight) as combined_score

OPTIONAL MATCH (node)<-[:NEXT_CHUNK]-(prev)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next)

RETURN {
    score: combined_score,
    central_node_content: node.page_content,
    central_node_chunk_id: node.chunk_id,
    central_node_chunk_id_consecutive: node.chunk_id_consecutive,
    surrounding_context: {
        previous_chunk_node_content: prev.page_content,
        previous_chunk_id: prev.chunk_id_consecutive,
        next_chunk_node_content: next.page_content,
        next_chunk_id: next.chunk_id_consecutive
    }
} as result
ORDER BY combined_score DESC
LIMIT $top_k
"""

# ============================================================================
# QUERIES DE CONFIGURACIÓN
# ============================================================================

SETUP_VECTOR_INDEX = """
CALL db.index.vector.createNodeIndex(
    'chunk_embeddings',
    'Chunk',
    'embeddings',
    384,
    'cosine'
)
"""

SETUP_FULLTEXT_INDEX = """
CREATE FULLTEXT INDEX chunk_content IF NOT EXISTS
FOR (c:Chunk)
ON EACH [c.page_content]
OPTIONS {
    indexConfig: {
        `fulltext.analyzer`: 'spanish',
        `fulltext.eventually_consistent`: false
    }
}
"""

SETUP_REGULAR_INDEX = """
CREATE INDEX chunk_consecutive_idx IF NOT EXISTS
FOR (c:Chunk)
ON (c.chunk_id_consecutive)
"""

# ============================================================================
# QUERIES DE VALIDACIÓN Y LIMPIEZA
# ============================================================================

VALIDATE_INDEXES = """
// Validar que todos los índices existen
CALL db.indexes() YIELD name, type, state, populationPercent
WHERE name IN ['chunk_embeddings', 'chunk_content', 'chunk_consecutive_idx']
RETURN name, type, state, populationPercent
ORDER BY name
"""

CLEAN_TEST_DATA = """
// Limpiar datos de prueba
MATCH (n)
WHERE n.chunk_id STARTS WITH 'test_' 
   OR n.filename STARTS WITH 'test_'
   OR n.name STARTS WITH 'test_'
DETACH DELETE n
"""

COUNT_PATTERN_NODES = """
// Contar nodos por patrón
MATCH (f:File)
WITH count(f) as files
MATCH (p:Page)
WITH files, count(p) as pages
MATCH (c:Chunk)
WITH files, pages, count(c) as chunks
MATCH (e:Entity)
RETURN files, pages, chunks, count(e) as entities
"""

