"""
Servicio para Graph Data Science (GDS) - Requiere módulo opcional ungraph[gds]

Este servicio proporciona funcionalidades avanzadas de análisis de grafos
usando Neo4j Graph Data Science Library.
"""

import logging
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class GDSService:
    """
    Servicio para operaciones de Graph Data Science.
    
    Requiere: pip install ungraph[gds]
    """
    
    def __init__(self, database: str = "neo4j"):
        """
        Inicializa el servicio GDS.
        
        Args:
            database: Nombre de la base de datos Neo4j
        """
        self.database = database
        self._driver = None
        self._gds_available = None
    
    def _get_driver(self) -> GraphDatabase:
        """Obtiene o crea el driver de Neo4j."""
        if self._driver is None:
            from src.utils.graph_operations import graph_session
            self._driver = graph_session()
        return self._driver
    
    def _check_gds_available(self) -> bool:
        """Verifica si GDS está disponible."""
        if self._gds_available is not None:
            return self._gds_available
        
        try:
            driver = self._get_driver()
            with driver.session(database=self.database) as session:
                result = session.run("RETURN gds.version() as version")
                version = result.single()["version"]
                logger.info(f"GDS version: {version}")
                self._gds_available = True
                return True
        except Exception as e:
            logger.warning(f"GDS not available: {e}")
            self._gds_available = False
            return False
    
    def detect_communities(
        self,
        graph_name: str = "chunk-graph",
        algorithm: str = "louvain",
        relationship_types: List[str] = None,
        write_property: str = "community_id"
    ) -> Dict[str, Any]:
        """
        Detecta comunidades en el grafo usando GDS.
        
        Args:
            graph_name: Nombre del grafo proyectado en GDS
            algorithm: Algoritmo a usar ("louvain" o "leiden")
            relationship_types: Tipos de relaciones a incluir (default: ["NEXT_CHUNK", "MENTIONS"])
            write_property: Nombre de la propiedad donde escribir el community_id
        
        Returns:
            Dict con estadísticas de las comunidades detectadas
        
        Raises:
            RuntimeError: Si GDS no está disponible
            ValueError: Si el algoritmo no es válido
        """
        if not self._check_gds_available():
            raise RuntimeError(
                "GDS is not available. Install with: pip install ungraph[gds] "
                "and ensure Neo4j GDS plugin is installed."
            )
        
        if algorithm not in ["louvain", "leiden"]:
            raise ValueError(f"Algorithm must be 'louvain' or 'leiden', got: {algorithm}")
        
        if relationship_types is None:
            relationship_types = ["NEXT_CHUNK", "MENTIONS"]
        
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                # 1. Crear grafo proyectado si no existe
                self._create_graph_projection(session, graph_name, relationship_types)
                
                # 2. Ejecutar algoritmo de detección de comunidades
                if algorithm == "louvain":
                    query = f"""
                    CALL gds.louvain.stream('{graph_name}')
                    YIELD nodeId, communityId
                    RETURN gds.util.asNode(nodeId) as node, communityId
                    """
                else:  # leiden
                    query = f"""
                    CALL gds.leiden.stream('{graph_name}')
                    YIELD nodeId, communityId
                    RETURN gds.util.asNode(nodeId) as node, communityId
                    """
                
                result = session.run(query)
                
                # 3. Escribir community_id de vuelta a los nodos
                write_query = f"""
                CALL gds.{algorithm}.write('{graph_name}', {{
                    writeProperty: '{write_property}'
                }})
                YIELD communityCount, ranIterations, didConverge
                RETURN communityCount, ranIterations, didConverge
                """
                
                write_result = session.run(write_query)
                stats = write_result.single()
                
                logger.info(f"Detected {stats['communityCount']} communities using {algorithm}")
                
                return {
                    "algorithm": algorithm,
                    "community_count": stats["communityCount"],
                    "iterations": stats["ranIterations"],
                    "converged": stats["didConverge"],
                    "write_property": write_property
                }
        except Exception as e:
            logger.error(f"Error detecting communities: {e}", exc_info=True)
            raise
    
    def _create_graph_projection(
        self,
        session,
        graph_name: str,
        relationship_types: List[str]
    ) -> None:
        """Crea un grafo proyectado en GDS si no existe."""
        # Verificar si el grafo ya existe
        check_query = "CALL gds.graph.exists($graph_name) YIELD exists"
        result = session.run(check_query, graph_name=graph_name)
        exists = result.single()["exists"]
        
        if exists:
            logger.info(f"Graph projection '{graph_name}' already exists")
            return
        
        # Crear grafo proyectado
        rel_types_str = ", ".join([f"'{rt}'" for rt in relationship_types])
        
        create_query = f"""
        CALL gds.graph.project(
            '{graph_name}',
            'Chunk',
            [{rel_types_str}]
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
        """
        
        result = session.run(create_query)
        stats = result.single()
        logger.info(
            f"Created graph projection '{graph_name}': "
            f"{stats['nodeCount']} nodes, {stats['relationshipCount']} relationships"
        )
    
    def close(self) -> None:
        """Cierra la conexión a Neo4j."""
        if self._driver:
            self._driver.close()
            self._driver = None




