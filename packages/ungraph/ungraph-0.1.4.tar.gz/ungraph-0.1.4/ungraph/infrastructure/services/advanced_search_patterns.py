"""
Patrones avanzados de búsqueda GraphRAG que requieren módulos opcionales.

Estos patrones usan Graph Data Science (GDS) y otras funcionalidades avanzadas.
Requieren instalar: pip install ungraph[gds]
"""

import re
from typing import Dict, Any, Tuple, List, Optional


class AdvancedSearchPatterns:
    """
    Patrones avanzados de búsqueda GraphRAG.
    
    Requiere módulo opcional: ungraph[gds]
    """
    
    @staticmethod
    def graph_enhanced_vector_search(
        query_text: str,
        query_vector: List[float],
        limit: int = 5,
        max_traversal_depth: int = 2,
        entity_label: str = "Entity",
        mentions_relationship: str = "MENTIONS"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Graph-Enhanced Vector Search: Combina búsqueda vectorial con traversal del grafo.
        
        Requiere: ungraph[gds] y entidades extraídas en el grafo.
        
        Cómo funciona:
        1. Busca chunks similares usando embeddings
        2. Extrae entidades mencionadas en esos chunks
        3. Hace traversal del grafo desde esas entidades
        4. Retorna contexto enriquecido
        
        Args:
            query_text: Texto a buscar (para full-text search)
            query_vector: Vector de embedding de la query
            limit: Número máximo de resultados
            max_traversal_depth: Profundidad máxima de traversal (1-3 recomendado)
            entity_label: Label de los nodos Entity
            mentions_relationship: Tipo de relación Chunk->Entity
        
        Returns:
            Tuple de (query_cypher, parameters_dict)
        
        Example:
            >>> from ungraph import HuggingFaceEmbeddingService
            >>> embedding_service = HuggingFaceEmbeddingService()
            >>> query_vector = embedding_service.generate_embedding("machine learning")
            >>> 
            >>> query, params = AdvancedSearchPatterns.graph_enhanced_vector_search(
            ...     "machine learning",
            ...     query_vector.vector,
            ...     limit=5,
            ...     max_traversal_depth=2
            ... )
        """
        # Validar parámetros
        if max_traversal_depth < 1 or max_traversal_depth > 5:
            raise ValueError("max_traversal_depth must be between 1 and 5")
        
        valid_label_pattern = re.compile(r'^[A-Z][a-zA-Z0-9_]*$')
        valid_rel_pattern = re.compile(r'^[A-Z][A-Z0-9_]*$')
        
        if not valid_label_pattern.match(entity_label):
            raise ValueError(f"Invalid entity_label: {entity_label}")
        if not valid_rel_pattern.match(mentions_relationship):
            raise ValueError(f"Invalid mentions_relationship: {mentions_relationship}")
        
        query = f"""
        // 1. Búsqueda vectorial inicial
        CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $query_vector)
        YIELD node as initial_chunk, score as initial_score
        
        // 2. Encontrar entidades mencionadas en chunks iniciales
        OPTIONAL MATCH (initial_chunk)-[:{mentions_relationship}]->(entity:{entity_label})
        
        // 3. Encontrar otros chunks relacionados a través de entidades
        // Traversal de profundidad variable
        OPTIONAL MATCH path = (entity)<-[:{mentions_relationship}]-(related_chunk:Chunk)
        WHERE related_chunk <> initial_chunk
        
        // 4. Agregar contexto de chunks relacionados
        WITH initial_chunk, initial_score, 
             collect(DISTINCT {{
                 chunk: related_chunk,
                 entity: entity.text,
                 path_length: length(path)
             }}) as related_context
        
        // 5. También buscar chunks vecinos (NEXT_CHUNK)
        OPTIONAL MATCH (initial_chunk)-[:NEXT_CHUNK]-(neighbor:Chunk)
        
        WITH initial_chunk, initial_score, related_context,
             collect(DISTINCT neighbor) as neighbors
        
        RETURN {{
            central_chunk: {{
                content: initial_chunk.page_content,
                chunk_id: initial_chunk.chunk_id,
                score: initial_score
            }},
            related_chunks: related_context,
            neighbor_chunks: [n IN neighbors | {{
                content: n.page_content,
                chunk_id: n.chunk_id
            }}]
        }} as result
        ORDER BY initial_score DESC
        LIMIT $limit
        """
        
        return query, {
            "query_text": query_text,
            "query_vector": query_vector,
            "limit": limit,
            "max_traversal_depth": max_traversal_depth
        }
    
    @staticmethod
    def local_retriever(
        query_text: str,
        limit: int = 5,
        community_threshold: int = 3,
        max_depth: int = 2
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Local Retriever: Búsqueda en subgrafos relacionados (comunidades pequeñas).
        
        Similar a Community Summary pero optimizado para comunidades más pequeñas.
        No requiere GDS, usa traversal básico de Cypher.
        
        Args:
            query_text: Texto a buscar
            limit: Número máximo de resultados
            community_threshold: Tamaño mínimo de comunidad
            max_depth: Profundidad máxima de relaciones (1-3 recomendado)
        
        Returns:
            Tuple de (query_cypher, parameters_dict)
        
        Example:
            >>> query, params = AdvancedSearchPatterns.local_retriever(
            ...     "neural networks",
            ...     limit=5,
            ...     community_threshold=3,
            ...     max_depth=1
            ... )
        """
        if max_depth < 1 or max_depth > 3:
            raise ValueError("max_depth must be between 1 and 3")
        
        query = f"""
        // 1. Buscar chunk central
        CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
        YIELD node as central_node, score
        
        // 2. Encontrar comunidad local (chunks relacionados)
        MATCH path = (central_node)-[*1..{max_depth}]-(community_node:Chunk)
        WHERE community_node <> central_node
        
        // 3. Agrupar por chunk central y contar comunidad
        WITH central_node, score,
             collect(DISTINCT community_node) as community,
             count(DISTINCT community_node) as community_size
        
        // 4. Filtrar por threshold mínimo
        WHERE community_size >= $community_threshold
        
        // 5. Construir resumen de comunidad
        WITH central_node, score, community, community_size,
             reduce(
                 summary = "",
                 node IN community |
                 summary + " " + coalesce(node.page_content, "")
             ) as community_text
        
        RETURN {{
            central_content: central_node.page_content,
            central_chunk_id: central_node.chunk_id,
            central_score: score,
            community_size: community_size,
            community_chunks: [n IN community | {{
                content: n.page_content,
                chunk_id: n.chunk_id
            }}],
            community_summary: trim(community_text)
        }} as result
        ORDER BY score DESC, community_size DESC
        LIMIT $limit
        """
        
        return query, {
            "query_text": query_text,
            "limit": limit,
            "community_threshold": community_threshold
        }
    
    @staticmethod
    def community_summary_retriever_gds(
        query_text: str,
        limit: int = 5,
        min_community_size: int = 5,
        algorithm: str = "louvain"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Community Summary Retriever usando Graph Data Science (GDS).
        
        Requiere: ungraph[gds] y Neo4j GDS plugin instalado.
        
        Usa algoritmos de detección de comunidades (Louvain, Leiden) para encontrar
        comunidades de chunks relacionados y generar resúmenes.
        
        Args:
            query_text: Texto a buscar
            limit: Número máximo de resultados
            min_community_size: Tamaño mínimo de comunidad
            algorithm: Algoritmo a usar ("louvain" o "leiden")
        
        Returns:
            Tuple de (query_cypher, parameters_dict)
        
        Note:
            Este query requiere que se haya ejecutado previamente:
            1. Crear grafo proyectado en GDS
            2. Ejecutar algoritmo de detección de comunidades
            3. Escribir comunidades de vuelta al grafo
        
        Example:
            >>> query, params = AdvancedSearchPatterns.community_summary_retriever_gds(
            ...     "machine learning",
            ...     limit=3,
            ...     min_community_size=5,
            ...     algorithm="louvain"
            ... )
        """
        if algorithm not in ["louvain", "leiden"]:
            raise ValueError("algorithm must be 'louvain' or 'leiden'")
        
        # Este query asume que las comunidades ya fueron calculadas y escritas
        # como propiedades en los nodos Chunk (ej: chunk.community_id)
        query = """
        // 1. Buscar chunk central
        CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
        YIELD node as central_node, score
        
        // 2. Encontrar comunidad del chunk central
        // Asume que chunk.community_id fue escrito por GDS
        MATCH (central_node:Chunk)
        WHERE central_node.community_id IS NOT NULL
        
        // 3. Encontrar todos los chunks de la misma comunidad
        MATCH (community_node:Chunk)
        WHERE community_node.community_id = central_node.community_id
          AND community_node <> central_node
        
        // 4. Agrupar y contar
        WITH central_node, score,
             collect(DISTINCT community_node) as community,
             count(DISTINCT community_node) as community_size
        
        // 5. Filtrar por tamaño mínimo
        WHERE community_size >= $min_community_size
        
        // 6. Construir resumen
        WITH central_node, score, community, community_size,
             reduce(
                 summary = "",
                 node IN community |
                 summary + " " + coalesce(node.page_content, "")
             ) as community_text
        
        RETURN {
            central_content: central_node.page_content,
            central_chunk_id: central_node.chunk_id,
            central_score: score,
            community_id: central_node.community_id,
            community_size: community_size,
            community_summary: trim(community_text)
        } as result
        ORDER BY score DESC, community_size DESC
        LIMIT $limit
        """
        
        return query, {
            "query_text": query_text,
            "limit": limit,
            "min_community_size": min_community_size
        }




