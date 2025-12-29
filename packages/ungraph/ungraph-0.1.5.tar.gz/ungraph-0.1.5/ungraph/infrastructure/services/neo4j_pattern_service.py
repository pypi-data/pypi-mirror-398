"""
Implementación: Neo4jPatternService

Implementa PatternService usando Neo4j.
Genera queries Cypher dinámicamente basado en patrones.

Estrategia:
- Si el patrón es FILE_PAGE_CHUNK, usa código existente (compatibilidad)
- Para otros patrones, genera queries dinámicamente

Referencias:
- Código existente: src/utils/graph_operations.py::extract_document_structure
- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/
"""

import logging
from typing import Dict, Any
from neo4j import GraphDatabase

from ungraph.domain.services.pattern_service import PatternService
from ungraph.domain.value_objects.graph_pattern import GraphPattern

# Importar funciones de graph_operations
# Usar import relativo para evitar problemas con src.__init__.py durante desarrollo
try:
    from ungraph.utils.graph_operations import graph_session, extract_document_structure
except ImportError:
    # Fallback para cuando se ejecuta desde diferentes contextos
    import sys
    from pathlib import Path
    utils_path = Path(__file__).parent.parent.parent / "utils"
    if str(utils_path) not in sys.path:
        sys.path.insert(0, str(utils_path))
    from graph_operations import graph_session, extract_document_structure

logger = logging.getLogger(__name__)


class Neo4jPatternService(PatternService):
    """
    Implementa PatternService usando Neo4j.
    
    Esta implementación:
    - Reutiliza código existente para FILE_PAGE_CHUNK (compatibilidad)
    - Genera queries dinámicamente para patrones nuevos
    - Valida patrones antes de aplicarlos
    """
    
    def __init__(self, database: str = "neo4j"):
        """
        Inicializa el servicio.
        
        Args:
            database: Nombre de la base de datos Neo4j (default: "neo4j")
        """
        self.database = database
        self._driver = None
    
    def apply_pattern(
        self,
        pattern: GraphPattern,
        data: Dict[str, Any]
    ) -> None:
        """
        Aplica un patrón al grafo.
        
        Si es FILE_PAGE_CHUNK, usa código existente (probado y funcionando).
        Si es otro patrón, genera query dinámicamente.
        """
        # Validar patrón primero
        if not self.validate_pattern(pattern):
            raise ValueError(f"Invalid pattern: {pattern.name}")
        
        driver = self._get_driver()
        
        if pattern.name == "FILE_PAGE_CHUNK":
            # Usar código existente - no reinventar la rueda
            # Esto garantiza compatibilidad y que el código probado siga funcionando
            with driver.session(database=self.database) as session:
                session.execute_write(extract_document_structure, **data)
            logger.info(f"Applied pattern {pattern.name} using existing implementation")
        else:
            # Generar query dinámicamente para patrones nuevos
            query = self.generate_cypher(pattern, "create")
            with driver.session(database=self.database) as session:
                session.run(query, **data)
            logger.info(f"Applied pattern {pattern.name} using generated query")
    
    def generate_cypher(
        self,
        pattern: GraphPattern,
        operation: str
    ) -> str:
        """
        Genera query Cypher dinámicamente.
        
        Soporta operaciones: "create", "search", "update", "delete"
        Por ahora solo implementamos "create" (mínimo viable).
        """
        if operation == "create":
            return self._generate_create_cypher(pattern)
        else:
            raise ValueError(f"Operation '{operation}' not yet implemented. Supported: 'create'")
    
    def _generate_create_cypher(self, pattern: GraphPattern) -> str:
        """
        Genera query MERGE para crear nodos y relaciones.
        
        Genera un query Cypher que:
        1. Crea/actualiza nodos usando MERGE
        2. Crea relaciones entre nodos
        3. Usa parámetros ($param) para todos los valores
        
        Returns:
            Query Cypher como string con placeholders $param
        """
        parts = []
        node_vars = {}  # Mapeo de label a variable
        
        # Generar MERGE para cada nodo
        for idx, node_def in enumerate(pattern.node_definitions):
            var_name = f"n{idx}"  # Variable única para cada nodo
            node_vars[node_def.label] = var_name
            
            # Construir propiedades requeridas
            required_props = []
            for prop_name in node_def.required_properties.keys():
                required_props.append(f"{prop_name}: ${prop_name}")
            
            required_props_str = ", ".join(required_props)
            
            # MERGE statement
            parts.append(f"MERGE ({var_name}:{node_def.label} {{{required_props_str}}})")
            
            # ON CREATE SET para propiedades opcionales
            optional_props = []
            for prop_name in node_def.optional_properties.keys():
                optional_props.append(f"{var_name}.{prop_name} = ${prop_name}")
            
            if optional_props:
                parts.append(f"ON CREATE SET {', '.join(optional_props)}")
        
        # Generar MERGE para relaciones
        for rel_def in pattern.relationship_definitions:
            from_var = node_vars[rel_def.from_node]
            to_var = node_vars[rel_def.to_node]
            
            # Construir propiedades de relación si existen
            rel_props = ""
            if rel_def.properties:
                rel_prop_list = [f"{k}: ${k}" for k in rel_def.properties.keys()]
                rel_props = f" {{{', '.join(rel_prop_list)}}}"
            
            if rel_def.direction == "OUTGOING":
                parts.append(f"MERGE ({from_var})-[:{rel_def.relationship_type}{rel_props}]->({to_var})")
            else:  # INCOMING
                parts.append(f"MERGE ({from_var})<-[:{rel_def.relationship_type}{rel_props}]-({to_var})")
        
        return "\n".join(parts)
    
    def validate_pattern(self, pattern: GraphPattern) -> bool:
        """
        Valida que un patrón sea correcto.
        
        Realiza validaciones adicionales:
        - Verifica que el patrón tenga nombre
        - Verifica que tenga al menos un nodo
        - Verifica que las relaciones referencien nodos válidos
        """
        try:
            # Validaciones básicas (ya están en GraphPattern.__post_init__)
            if not pattern.name:
                logger.error("Pattern name is empty")
                return False
            
            if not pattern.node_definitions:
                logger.error("Pattern has no node definitions")
                return False
            
            # Validar que todas las relaciones referencian nodos válidos
            node_labels = {node.label for node in pattern.node_definitions}
            for rel_def in pattern.relationship_definitions:
                if rel_def.from_node not in node_labels:
                    logger.error(f"Relationship references unknown from_node: {rel_def.from_node}")
                    return False
                if rel_def.to_node not in node_labels:
                    logger.error(f"Relationship references unknown to_node: {rel_def.to_node}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating pattern: {e}", exc_info=True)
            return False
    
    def _get_driver(self) -> GraphDatabase:
        """Obtiene o crea el driver de Neo4j."""
        if self._driver is None:
            self._driver = graph_session()
        return self._driver
    
    def close(self) -> None:
        """Cierra la conexión a Neo4j."""
        if self._driver:
            self._driver.close()
            self._driver = None

