"""
Implementación: Neo4jIndexService

Implementa IndexService usando Neo4j.
Envuelve el código existente de graph_operations.py.
"""

import logging
import os
from neo4j import GraphDatabase

from domain.services.index_service import IndexService
from ...utils.graph_operations import graph_session

logger = logging.getLogger(__name__) 


class Neo4jIndexService(IndexService):
    """
    Implementación de IndexService usando Neo4j.
    
    Crea índices vectoriales, full-text y regulares en Neo4j.
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
    
    def setup_vector_index(
        self,
        index_name: str,
        node_label: str,
        property_name: str,
        dimensions: int
    ) -> None:
        """
        Crea un índice vectorial en Neo4j.
        
        Basado en setup_advanced_indexes del notebook.
        """
        query = f"""
        CALL db.index.vector.createNodeIndex(
            '{index_name}',
            '{node_label}',
            '{property_name}',
            {dimensions},
            'cosine'
        )
        """
        
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                session.execute_write(lambda tx: tx.run(query))
                logger.info(f"Vector index '{index_name}' created successfully")
        except Exception as e:
            msg = str(e)
            # Fallback to default DB if the configured DB does not exist
            if "DatabaseNotFound" in msg or "graph reference" in msg:
                fallback_db = os.environ.get("NEO4J_DB", "neo4j")
                logger.warning(f"Database '{self.database}' not found; falling back to '{fallback_db}' for vector index creation")
                try:
                    with driver.session(database=fallback_db) as session:
                        session.execute_write(lambda tx: tx.run(query))
                        logger.info(f"Vector index '{index_name}' created successfully in fallback DB '{fallback_db}'")
                except Exception as e2:
                    msg2 = str(e2)
                    if "EquivalentSchemaRuleAlreadyExistsException" in msg2 or "equivalent index" in msg2 or "An equivalent index already exists" in msg2:
                        logger.info(f"Vector index '{index_name}' already exists in fallback DB '{fallback_db}'")
                    else:
                        logger.error(f"Error creating vector index in fallback DB '{fallback_db}': {e2}")
                        raise
            else:
                if "An equivalent index already exists" not in msg:
                    logger.error(f"Error creating vector index: {e}")
                    raise
                logger.info(f"Vector index '{index_name}' already exists")
    
    def setup_fulltext_index(
        self,
        index_name: str,
        node_label: str,
        property_name: str,
        analyzer: str = "spanish"
    ) -> None:
        """
        Crea un índice full-text en Neo4j.
        
        Basado en setup_advanced_indexes del notebook.
        """
        query = f"""
        CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
        FOR (c:{node_label})
        ON EACH [c.{property_name}]
        OPTIONS {{
            indexConfig: {{
                `fulltext.analyzer`: '{analyzer}',
                `fulltext.eventually_consistent`: false
            }}
        }}
        """
        
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                session.execute_write(lambda tx: tx.run(query))
                logger.info(f"Full-text index '{index_name}' created successfully")
        except Exception as e:
            msg = str(e)
            if "DatabaseNotFound" in msg or "graph reference" in msg:
                fallback_db = os.environ.get("NEO4J_DB", "neo4j")
                logger.warning(f"Database '{self.database}' not found; falling back to '{fallback_db}' for full-text index creation")
                try:
                    with driver.session(database=fallback_db) as session:
                        session.execute_write(lambda tx: tx.run(query))
                        logger.info(f"Full-text index '{index_name}' created successfully in fallback DB '{fallback_db}'")
                except Exception as e2:
                    logger.warning(f"Full-text index creation message in fallback DB: {e2}")
            else:
                logger.warning(f"Full-text index creation message: {e}")
    
    def setup_regular_index(
        self,
        index_name: str,
        node_label: str,
        property_name: str
    ) -> None:
        """
        Crea un índice regular en Neo4j.
        
        Basado en setup_advanced_indexes del notebook.
        """
        query = f"""
        CREATE INDEX {index_name} IF NOT EXISTS
        FOR (c:{node_label})
        ON (c.{property_name})
        """
        
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                session.execute_write(lambda tx: tx.run(query))
                logger.info(f"Regular index '{index_name}' created successfully")
        except Exception as e:
            msg = str(e)
            if "DatabaseNotFound" in msg or "graph reference" in msg:
                fallback_db = os.environ.get("NEO4J_DB", "neo4j")
                logger.warning(f"Database '{self.database}' not found; falling back to '{fallback_db}' for regular index creation")
                try:
                    with driver.session(database=fallback_db) as session:
                        session.execute_write(lambda tx: tx.run(query))
                        logger.info(f"Regular index '{index_name}' created successfully in fallback DB '{fallback_db}'")
                except Exception as e2:
                    logger.warning(f"Regular index creation message in fallback DB: {e2}")
            else:
                logger.warning(f"Regular index creation message: {e}")
    
    def setup_all_indexes(self) -> None:
        """
        Configura todos los índices necesarios.
        
        Basado en setup_advanced_indexes del notebook.
        """
        logger.info("Setting up all indexes")
        
        # Índice regular para chunk_id_consecutive
        self.setup_regular_index(
            "chunk_consecutive_idx",
            "Chunk",
            "chunk_id_consecutive"
        )
        
        # Índice vectorial para embeddings
        self.setup_vector_index(
            "chunk_embeddings",
            "Chunk",
            "embeddings",
            384
        )
        
        # Índice full-text para page_content
        self.setup_fulltext_index(
            "chunk_content",
            "Chunk",
            "page_content",
            "spanish"
        )
        
        logger.info("All indexes setup completed")
    
    def drop_index(self, index_name: str) -> None:
        """
        Elimina un índice específico.
        
        Args:
            index_name: Nombre del índice a eliminar
        
        Raises:
            ValueError: Si el índice no existe o no se puede eliminar
        """
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                # Intentar eliminar como índice regular/fulltext primero
                query = f"DROP INDEX {index_name} IF EXISTS"
                try:
                    session.execute_write(lambda tx: tx.run(query))
                    logger.info(f"Index '{index_name}' dropped successfully")
                    return
                except Exception:
                    pass
                
                # Si falla, intentar como índice vectorial
                query = f"CALL db.index.vector.drop('{index_name}')"
                try:
                    session.execute_write(lambda tx: tx.run(query))
                    logger.info(f"Vector index '{index_name}' dropped successfully")
                except Exception as e:
                    logger.warning(f"Could not drop index '{index_name}': {e}")
        except Exception as e:
            logger.error(f"Error dropping index '{index_name}': {e}")
            raise
    
    def drop_all_indexes(self) -> None:
        """
        Elimina todos los índices creados por el sistema.
        
        Esto incluye:
        - Índices vectoriales (chunk_embeddings)
        - Índices full-text (chunk_content)
        - Índices regulares (chunk_consecutive_idx)
        """
        logger.info("Dropping all indexes")
        
        indexes_to_drop = [
            "chunk_embeddings",  # Vector index
            "chunk_content",     # Full-text index
            "chunk_consecutive_idx"  # Regular index
        ]
        
        for index_name in indexes_to_drop:
            try:
                self.drop_index(index_name)
            except Exception as e:
                logger.warning(f"Could not drop index '{index_name}': {e}")
        
        logger.info("All indexes dropped")
    
    def clean_graph(self, node_labels: list = None) -> None:
        """
        Limpia el grafo eliminando nodos y relaciones.
        
        Args:
            node_labels: Lista de labels de nodos a eliminar. 
                        Si es None, elimina todos los nodos y relaciones.
                        Si se especifica, solo elimina nodos con esos labels.
        
        Raises:
            Exception: Si ocurre un error durante la limpieza
        """
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                if node_labels:
                    # Eliminar solo nodos con labels específicos
                    for label in node_labels:
                        query = f"MATCH (n:{label}) DETACH DELETE n"
                        result = session.execute_write(lambda tx: tx.run(query))
                        count = result.consume().counters.nodes_deleted
                        logger.info(f"Deleted {count} nodes with label '{label}'")
                else:
                    # Eliminar todos los nodos y relaciones
                    query = "MATCH (n) DETACH DELETE n"
                    result = session.execute_write(lambda tx: tx.run(query))
                    count = result.consume().counters.nodes_deleted
                    logger.info(f"Deleted {count} nodes and all relationships")
        except Exception as e:
            logger.error(f"Error cleaning graph: {e}")
            raise
    
    def close(self) -> None:
        """Cierra la conexión a Neo4j."""
        if self._driver:
            self._driver.close()
            self._driver = None

