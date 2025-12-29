"""
Implementación: Neo4jSearchService

Implementa SearchService usando Neo4j.
Envuelve el código existente de graph_rags.py.
"""

import logging
from typing import List, Tuple
from neo4j import GraphDatabase

from ungraph.domain.services.search_service import SearchService, SearchResult
from ungraph.domain.value_objects.embedding import Embedding
from ungraph.utils.graph_operations import graph_session
from ungraph.infrastructure.services.graphrag_search_patterns import GraphRAGSearchPatterns

logger = logging.getLogger(__name__)


class Neo4jSearchService(SearchService):
    """
    Implementación de SearchService usando Neo4j.
    
    Soporta búsqueda por texto, vectorial e híbrida.
    Basado en graph_rags.py del código existente.
    """
    
    def __init__(self, database: str = "neo4j"):
        """
        Inicializa el servicio.
        
        Args:
            database: Nombre de la base de datos Neo4j (default: "neo4j")
        """
        self.database = database
        self._driver = None
    
    def _get_driver(self) -> GraphDatabase:
        """Obtiene o crea el driver de Neo4j."""
        if self._driver is None:
            self._driver = graph_session()
        return self._driver
    
    def text_search(
        self,
        query_text: str,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Búsqueda por texto usando índice full-text.
        
        Basado en text_search de graph_rags.py.
        """
        if not query_text:
            raise ValueError("Query text cannot be empty")
        
        search_query = """
        CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
        YIELD node, score
        RETURN node.page_content as content, 
               score,
               node.chunk_id as chunk_id,
               node.chunk_id_consecutive as chunk_id_consecutive
        ORDER BY score DESC
        LIMIT $limit
        """
        
        driver = self._get_driver()
        results = []
        
        try:
            with driver.session(database=self.database) as session:
                records = session.run(search_query, query_text=query_text, limit=limit)
                
                for record in records:
                    result = SearchResult(
                        content=record["content"],
                        score=float(record["score"]),
                        chunk_id=record["chunk_id"],
                        chunk_id_consecutive=record["chunk_id_consecutive"] or 0
                    )
                    results.append(result)
        except Exception as e:
            logger.error(f"Error in text search: {e}", exc_info=True)
            raise
        
        return results
    
    def vector_search(
        self,
        query_embedding: Embedding,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Búsqueda vectorial usando embeddings.
        
        Basado en hybrid_search de graph_rags.py.
        """
        query = """
        CALL db.index.vector.queryNodes('chunk_embeddings', toInteger($top_k), $query_vector)
        YIELD node, score
        
        OPTIONAL MATCH (node)<-[:NEXT_CHUNK]-(prev)
        OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next)
        
        RETURN {
            score: score,
            central_node_content: node.page_content,
            central_node_chunk_id: node.chunk_id,
            central_node_chunk_id_consecutive: node.chunk_id_consecutive,
            previous_chunk_content: prev.page_content,
            next_chunk_content: next.page_content
        } as result
        ORDER BY score DESC
        LIMIT $top_k
        """
        
        driver = self._get_driver()
        results = []
        
        try:
            with driver.session(database=self.database) as session:
                records = session.run(
                    query,
                    query_vector=query_embedding.vector,
                    top_k=limit
                )
                
                for record in records:
                    result_data = record["result"]
                    result = SearchResult(
                        content=result_data["central_node_content"],
                        score=float(result_data["score"]),
                        chunk_id=result_data["central_node_chunk_id"],
                        chunk_id_consecutive=result_data["central_node_chunk_id_consecutive"] or 0,
                        previous_chunk_content=result_data.get("previous_chunk_content"),
                        next_chunk_content=result_data.get("next_chunk_content")
                    )
                    results.append(result)
        except Exception as e:
            logger.error(f"Error in vector search: {e}", exc_info=True)
            raise
        
        return results
    
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: Embedding,
        weights: Tuple[float, float] = (0.3, 0.7),
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Búsqueda híbrida combinando texto y vectorial.
        
        Basado en hybrid_search de graph_rags.py.
        """
        if not query_text:
            raise ValueError("Query text cannot be empty")
        
        if len(weights) != 2:
            raise ValueError("Weights must be a tuple of 2 floats")
        
        text_weight, vector_weight = weights
        
        query = """
        // Búsqueda fulltext
        CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
        YIELD node as text_node, score as text_score
        
        // Combinar con búsqueda vectorial
        CALL {
            WITH text_node
            CALL db.index.vector.queryNodes('chunk_embeddings', toInteger($top_k), $query_vector)
            YIELD node as vec_node, score as vec_score
            WHERE text_node = vec_node
            RETURN vec_node, vec_score
        }
        
        // Calcular score combinado
        WITH text_node as node, text_score, vec_score,
             (text_score * $text_weight + vec_score * $vector_weight) as combined_score
        
        // Obtener contexto
        OPTIONAL MATCH (node)<-[:NEXT_CHUNK]-(prev)
        OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next)
        
        RETURN {
            score: combined_score,
            central_node_content: node.page_content,
            central_node_chunk_id: node.chunk_id,
            central_node_chunk_id_consecutive: node.chunk_id_consecutive,
            previous_chunk_content: prev.page_content,
            next_chunk_content: next.page_content
        } as result
        ORDER BY combined_score DESC
        LIMIT $top_k
        """
        
        driver = self._get_driver()
        results = []
        
        try:
            with driver.session(database=self.database) as session:
                records = session.run(
                    query,
                    query_text=query_text,
                    query_vector=query_embedding.vector,
                    text_weight=text_weight,
                    vector_weight=vector_weight,
                    top_k=limit
                )
                
                for record in records:
                    result_data = record["result"]
                    result = SearchResult(
                        content=result_data["central_node_content"],
                        score=float(result_data["score"]),
                        chunk_id=result_data["central_node_chunk_id"],
                        chunk_id_consecutive=result_data["central_node_chunk_id_consecutive"] or 0,
                        previous_chunk_content=result_data.get("previous_chunk_content"),
                        next_chunk_content=result_data.get("next_chunk_content")
                    )
                    results.append(result)
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}", exc_info=True)
            raise
        
        return results
    
    def search_with_pattern(
        self,
        query_text: str,
        pattern_type: str,
        limit: int = 5,
        **kwargs
    ) -> List[SearchResult]:
        """
        Búsqueda usando un patrón GraphRAG específico.
        
        Args:
            query_text: Texto a buscar
            pattern_type: Tipo de patrón ("metadata_filtering", "parent_child")
            limit: Número máximo de resultados
            **kwargs: Parámetros específicos del patrón
        
        Returns:
            Lista de SearchResult
        
        Raises:
            ValueError: Si el pattern_type no es válido o los parámetros son incorrectos
        
        Example:
            >>> # Búsqueda con filtros de metadatos
            >>> results = service.search_with_pattern(
            ...     "machine learning",
            ...     pattern_type="metadata_filtering",
            ...     metadata_filters={"filename": "ai_paper.md"}
            ... )
            >>>
            >>> # Búsqueda parent-child
            >>> results = service.search_with_pattern(
            ...     "inteligencia artificial",
            ...     pattern_type="parent_child",
            ...     parent_label="Page",
            ...     child_label="Chunk"
            ... )
        """
        if not query_text:
            raise ValueError("Query text cannot be empty")
        
        # Mapear nombres de patrones a métodos (más explícito y seguro)
        pattern_map = {
            "basic": GraphRAGSearchPatterns.basic_retriever,
            "basic_retriever": GraphRAGSearchPatterns.basic_retriever,  # Alias
            "metadata_filtering": GraphRAGSearchPatterns.metadata_filtering,
            "parent_child": GraphRAGSearchPatterns.parent_child_retriever,
            "parent_child_retriever": GraphRAGSearchPatterns.parent_child_retriever,  # Alias
        }
        
        # Patrones avanzados (requieren módulos opcionales)
        try:
            from .advanced_search_patterns import AdvancedSearchPatterns
            pattern_map.update({
                "graph_enhanced": AdvancedSearchPatterns.graph_enhanced_vector_search,
                "graph_enhanced_vector": AdvancedSearchPatterns.graph_enhanced_vector_search,
                "local": AdvancedSearchPatterns.local_retriever,
                "local_retriever": AdvancedSearchPatterns.local_retriever,
                "community_summary": AdvancedSearchPatterns.community_summary_retriever_gds,
                "community_summary_gds": AdvancedSearchPatterns.community_summary_retriever_gds,
            })
        except ImportError:
            # Módulos avanzados no disponibles, solo patrones básicos
            pass
        
        pattern_method = pattern_map.get(pattern_type)
        if not pattern_method:
            raise ValueError(
                f"Unknown pattern type: {pattern_type}. "
                f"Available: {', '.join(pattern_map.keys())}"
            )
        
        # Generar query y parámetros
        # Para graph_enhanced, necesita query_vector que debe generarse
        if pattern_type in ["graph_enhanced", "graph_enhanced_vector"]:
            if "query_vector" not in kwargs:
                # Generar embedding si no se proporciona
                from ungraph.infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
                from ungraph.core.configuration import get_settings
                settings = get_settings()
                embedding_service = HuggingFaceEmbeddingService(model_name=settings.embedding_model)
                embedding = embedding_service.generate_embedding(query_text)
                kwargs["query_vector"] = embedding.vector
        
        query, params = pattern_method(query_text, limit=limit, **kwargs)
        
        # Ejecutar query
        driver = self._get_driver()
        results = []
        
        try:
            with driver.session(database=self.database) as session:
                records = session.run(query, **params)
                
                for record in records:
                    # Manejar diferentes formatos de resultado según el patrón
                    if pattern_type in ["basic", "basic_retriever"]:
                        result = SearchResult(
                            content=record["content"],
                            score=float(record["score"]),
                            chunk_id=record["chunk_id"],
                            chunk_id_consecutive=record["chunk_id_consecutive"] or 0
                        )
                        results.append(result)
                    
                    elif pattern_type == "metadata_filtering":
                        result = SearchResult(
                            content=record["content"],
                            score=float(record["score"]),
                            chunk_id=record["chunk_id"],
                            chunk_id_consecutive=record["chunk_id_consecutive"] or 0
                        )
                        results.append(result)
                    
                    elif pattern_type in ["parent_child", "parent_child_retriever"]:
                        # Para parent_child, el resultado tiene estructura diferente
                        result_data = record["result"]
                        children_content = [c['content'] for c in result_data['children']]
                        # Crear un SearchResult que represente el padre y su contexto de hijos
                        result = SearchResult(
                            content=result_data["parent_content"],
                            score=float(result_data["parent_score"]),
                            chunk_id=result_data["parent_chunk_id"],
                            chunk_id_consecutive=0,  # No aplica para parent
                            next_chunk_content=" ".join(children_content)  # Concatenar hijos como contexto
                        )
                        results.append(result)
                    
                    elif pattern_type in ["graph_enhanced", "graph_enhanced_vector"]:
                        # Graph-Enhanced retorna estructura compleja
                        result_data = record["result"]
                        central = result_data["central_chunk"]
                        related_text = " ".join([
                            ctx.get("chunk", {}).get("content", "") 
                            for ctx in result_data.get("related_chunks", [])
                        ])
                        neighbor_text = " ".join([
                            n.get("content", "") 
                            for n in result_data.get("neighbor_chunks", [])
                        ])
                        full_context = f"{related_text} {neighbor_text}".strip()
                        
                        result = SearchResult(
                            content=central["content"],
                            score=float(central["score"]),
                            chunk_id=central["chunk_id"],
                            chunk_id_consecutive=0,
                            next_chunk_content=full_context if full_context else None
                        )
                        results.append(result)
                    
                    elif pattern_type in ["local", "local_retriever"]:
                        # Local retriever retorna estructura con comunidad
                        result_data = record["result"]
                        result = SearchResult(
                            content=result_data["central_content"],
                            score=float(result_data["central_score"]),
                            chunk_id=result_data["central_chunk_id"],
                            chunk_id_consecutive=0,
                            next_chunk_content=result_data.get("community_summary", "")
                        )
                        results.append(result)
                    
                    elif pattern_type in ["community_summary", "community_summary_gds"]:
                        # Community Summary retorna estructura con resumen
                        result_data = record["result"]
                        result = SearchResult(
                            content=result_data["central_content"],
                            score=float(result_data["central_score"]),
                            chunk_id=result_data["central_chunk_id"],
                            chunk_id_consecutive=0,
                            next_chunk_content=result_data.get("community_summary", "")
                        )
                        results.append(result)
                    
                    else:
                        # Manejo genérico si el patrón retorna un formato simple
                        if "content" in record and "score" in record:
                            result = SearchResult(
                                content=record["content"],
                                score=float(record["score"]),
                                chunk_id=record.get("chunk_id", "unknown"),
                                chunk_id_consecutive=record.get("chunk_id_consecutive", 0)
                            )
                            results.append(result)
                        else:
                            logger.warning(f"Unhandled result format for pattern {pattern_type}: {record}")
                            results.append(SearchResult(
                                content=str(record),  # Fallback a string
                                score=0.0,
                                chunk_id="unknown",
                                chunk_id_consecutive=0
                            ))
        
        except Exception as e:
            logger.error(f"Error in search_with_pattern ({pattern_type}): {e}", exc_info=True)
            raise
        
        return results
    
    def close(self) -> None:
        """Cierra la conexión a Neo4j."""
        if self._driver:
            self._driver.close()
            self._driver = None

