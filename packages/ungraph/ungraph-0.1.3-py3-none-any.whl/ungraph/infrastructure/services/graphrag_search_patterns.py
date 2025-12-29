"""
Patrones de búsqueda GraphRAG para Neo4j.

Implementación minimalista: solo patrones básicos más útiles.
Cada método retorna (query_cypher, parameters_dict) para ejecución segura.

Referencias:
- GraphRAG Pattern Catalog: https://graphrag.com/reference/
- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/
"""

import re
from typing import Dict, Any, Tuple, List


class GraphRAGSearchPatterns:
    """
    Patrones de búsqueda GraphRAG validados para Neo4j.
    
    Cada método retorna (query_cypher, parameters_dict) para ejecución segura.
    Todos los queries usan parámetros para prevenir inyección Cypher.
    """
    
    @staticmethod
    def basic_retriever(
        query_text: str,
        limit: int = 5
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Búsqueda full-text simple usando índice de texto completo.
        
        Este es el patrón más básico y rápido. Útil para búsquedas por palabras clave.
        
        Args:
            query_text: Texto a buscar
            limit: Número máximo de resultados
        
        Returns:
            Tuple de (query_cypher, parameters_dict)
        
        Example:
            >>> query, params = GraphRAGSearchPatterns.basic_retriever(
            ...     "computación cuántica",
            ...     limit=5
            ... )
        """
        query = """
        CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
        YIELD node, score
        RETURN node.page_content as content,
               score,
               node.chunk_id as chunk_id,
               node.chunk_id_consecutive as chunk_id_consecutive
        ORDER BY score DESC
        LIMIT $limit
        """
        
        return query, {
            "query_text": query_text,
            "limit": limit
        }
    
    @staticmethod
    def metadata_filtering(
        query_text: str,
        metadata_filters: Dict[str, Any],
        limit: int = 5
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Búsqueda full-text con filtros por metadatos.
        
        Útil para buscar solo en documentos específicos o filtrar por propiedades.
        
        Args:
            query_text: Texto a buscar
            metadata_filters: Dict con propiedades a filtrar (ej: {"filename": "doc.md"})
            limit: Número máximo de resultados
        
        Returns:
            Tuple de (query_cypher, parameters_dict)
        
        Example:
            >>> query, params = GraphRAGSearchPatterns.metadata_filtering(
            ...     "machine learning",
            ...     {"filename": "ai_paper.md", "page_number": 1}
            ... )
        """
        # Validar nombres de propiedades (solo alfanuméricos y underscore)
        valid_prop_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        for key in metadata_filters.keys():
            if not valid_prop_pattern.match(key):
                raise ValueError(f"Invalid property name: {key}")
        
        # Construir condiciones de filtro usando parámetros
        filter_conditions = " AND ".join([
            f"node.{key} = ${key}" for key in metadata_filters.keys()
        ])
        
        query = f"""
        CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
        YIELD node, score
        WHERE {filter_conditions}
        RETURN node.page_content as content,
               score,
               node.chunk_id as chunk_id,
               node.chunk_id_consecutive as chunk_id_consecutive
        ORDER BY score DESC
        LIMIT $limit
        """
        
        params = {
            "query_text": query_text,
            "limit": limit,
            **metadata_filters
        }
        return query, params
    
    @staticmethod
    def parent_child_retriever(
        query_text: str,
        parent_label: str = "Page",
        child_label: str = "Chunk",
        relationship_type: str = "HAS_CHUNK",
        limit: int = 5
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Busca en nodos padre y expande a todos sus hijos relacionados.
        
        Útil cuando necesitas contexto completo de una sección o página.
        
        Args:
            query_text: Texto a buscar
            parent_label: Label del nodo padre (default: "Page")
            child_label: Label del nodo hijo (default: "Chunk")
            relationship_type: Tipo de relación (default: "HAS_CHUNK")
            limit: Número máximo de resultados
        
        Returns:
            Tuple de (query_cypher, parameters_dict)
        
        Example:
            >>> query, params = GraphRAGSearchPatterns.parent_child_retriever(
            ...     "inteligencia artificial",
            ...     parent_label="Page",
            ...     child_label="Chunk"
            ... )
        """
        # Validar labels y relationship type
        # Labels pueden ser PascalCase (Page, Chunk) o UPPERCASE (FILE, PAGE)
        valid_label_pattern = re.compile(r'^[A-Z][a-zA-Z0-9_]*$')
        valid_rel_pattern = re.compile(r'^[A-Z][A-Z0-9_]*$')  # Relationship types deben ser UPPERCASE
        
        if not valid_label_pattern.match(parent_label):
            raise ValueError(f"Invalid parent_label: {parent_label}")
        if not valid_label_pattern.match(child_label):
            raise ValueError(f"Invalid child_label: {child_label}")
        if not valid_rel_pattern.match(relationship_type):
            raise ValueError(f"Invalid relationship_type: {relationship_type}")
        
        query = f"""
        CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
        YIELD node as parent_node, score as parent_score
        
        OPTIONAL MATCH (parent_node:{parent_label})-[:{relationship_type}]->(child_node:{child_label})

        WITH parent_node, parent_score, collect(DISTINCT {{
            content: child_node.page_content,
            chunk_id: child_node.chunk_id
        }}) as children

        RETURN {{
            parent_content: parent_node.page_content,
            parent_score: parent_score,
            parent_chunk_id: parent_node.chunk_id,
            children: children
        }} as result,
        parent_score
        ORDER BY parent_score DESC
        LIMIT $limit
        """
        
        return query, {
            "query_text": query_text,
            "limit": limit
        }

