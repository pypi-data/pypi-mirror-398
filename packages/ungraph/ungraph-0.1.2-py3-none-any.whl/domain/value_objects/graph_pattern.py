"""
Value Objects para definir patrones de grafo.

Estos objetos permiten definir estructuras de grafo de manera declarativa,
siguiendo principios de Clean Architecture y Domain-Driven Design.

Referencias:
- GraphRAG Pattern Catalog: https://graphrag.com/reference/
- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import re


@dataclass(frozen=True)
class NodeDefinition:
    """
    Define un tipo de nodo en el patrón de grafo.
    
    Un NodeDefinition especifica:
    - El label del nodo en Neo4j
    - Las propiedades requeridas y opcionales
    - Qué propiedades deben ser indexadas
    
    Attributes:
        label: Label del nodo en Neo4j (ej: "File", "Chunk")
        required_properties: Dict de propiedades obligatorias {nombre: tipo}
        optional_properties: Dict de propiedades opcionales {nombre: tipo}
        indexes: Lista de nombres de propiedades a indexar
    
    Example:
        >>> file_node = NodeDefinition(
        ...     label="File",
        ...     required_properties={"filename": str},
        ...     optional_properties={"createdAt": int},
        ...     indexes=["filename"]
        ... )
    """
    label: str
    required_properties: Dict[str, type] = field(default_factory=dict)
    optional_properties: Dict[str, type] = field(default_factory=dict)
    indexes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Valida que el NodeDefinition sea correcto."""
        if not self.label:
            raise ValueError("Node label cannot be empty")
        
        # Validar formato del label (debe seguir convenciones Neo4j)
        # Labels pueden ser PascalCase o UPPERCASE, con números y underscores
        if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', self.label):
            raise ValueError(
                f"Invalid label format: {self.label}. "
                "Labels must start with uppercase letter and contain only letters, numbers, and underscores."
            )
        
        # Validar que los nombres de propiedades son válidos
        all_props = set(self.required_properties.keys()) | set(self.optional_properties.keys())
        prop_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        for prop_name in all_props:
            if not prop_pattern.match(prop_name):
                raise ValueError(f"Invalid property name: {prop_name}")
        
        # Validar que los índices referencian propiedades existentes
        all_prop_names = set(self.required_properties.keys()) | set(self.optional_properties.keys())
        for index_prop in self.indexes:
            if index_prop not in all_prop_names:
                raise ValueError(f"Index property '{index_prop}' not found in node properties")


@dataclass(frozen=True)
class RelationshipDefinition:
    """
    Define una relación en el patrón de grafo.
    
    Un RelationshipDefinition especifica:
    - Los nodos origen y destino
    - El tipo de relación
    - Las propiedades de la relación (opcional)
    - La dirección de la relación
    
    Attributes:
        from_node: Label del nodo origen
        to_node: Label del nodo destino
        relationship_type: Tipo de relación (ej: "CONTAINS", "HAS_CHUNK")
        properties: Dict de propiedades de la relación {nombre: tipo}
        direction: Dirección de la relación ("OUTGOING" o "INCOMING")
    
    Example:
        >>> contains_rel = RelationshipDefinition(
        ...     from_node="File",
        ...     to_node="Page",
        ...     relationship_type="CONTAINS",
        ...     direction="OUTGOING"
        ... )
    """
    from_node: str
    to_node: str
    relationship_type: str
    properties: Dict[str, type] = field(default_factory=dict)
    direction: str = "OUTGOING"
    
    def __post_init__(self):
        """Valida que el RelationshipDefinition sea correcto."""
        if not self.from_node:
            raise ValueError("from_node cannot be empty")
        if not self.to_node:
            raise ValueError("to_node cannot be empty")
        if not self.relationship_type:
            raise ValueError("relationship_type cannot be empty")
        
        # Validar formato de relationship type
        # Relationship types pueden ser PascalCase o UPPERCASE
        if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', self.relationship_type):
            raise ValueError(
                f"Invalid relationship_type format: {self.relationship_type}. "
                "Relationship types must start with uppercase letter and contain only letters, numbers, and underscores."
            )
        
        # Validar dirección
        if self.direction not in ["OUTGOING", "INCOMING"]:
            raise ValueError(f"Invalid direction: {self.direction}. Must be 'OUTGOING' or 'INCOMING'")
        
        # Validar nombres de propiedades
        prop_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        for prop_name in self.properties.keys():
            if not prop_pattern.match(prop_name):
                raise ValueError(f"Invalid relationship property name: {prop_name}")


@dataclass(frozen=True)
class GraphPattern:
    """
    Patrón completo de estructura de grafo.
    
    Un GraphPattern define:
    - Los tipos de nodos que forman el patrón
    - Las relaciones entre nodos
    - Un template Cypher opcional para persistencia
    - Patrones de búsqueda asociados
    
    Attributes:
        name: Nombre único del patrón
        description: Descripción del patrón
        node_definitions: Lista de definiciones de nodos
        relationship_definitions: Lista de definiciones de relaciones
        cypher_template: Template Cypher opcional para persistencia
        search_patterns: Lista de patrones de búsqueda asociados
    
    Example:
        >>> pattern = GraphPattern(
        ...     name="FILE_PAGE_CHUNK",
        ...     description="Patrón básico: File contiene Pages, Pages contienen Chunks",
        ...     node_definitions=[file_node, page_node, chunk_node],
        ...     relationship_definitions=[contains_rel, has_chunk_rel]
        ... )
    """
    name: str
    description: str
    node_definitions: List[NodeDefinition]
    relationship_definitions: List[RelationshipDefinition]
    cypher_template: Optional[str] = None
    search_patterns: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Valida que el GraphPattern sea correcto."""
        if not self.name:
            raise ValueError("Pattern name cannot be empty")
        if not self.description:
            raise ValueError("Pattern description cannot be empty")
        if not self.node_definitions:
            raise ValueError("Pattern must have at least one node definition")
        
        # Validar que los relationship definitions referencian nodos válidos
        node_labels = {node_def.label for node_def in self.node_definitions}
        for rel_def in self.relationship_definitions:
            if rel_def.from_node not in node_labels:
                raise ValueError(
                    f"Relationship references unknown node '{rel_def.from_node}'. "
                    f"Available nodes: {node_labels}"
                )
            if rel_def.to_node not in node_labels:
                raise ValueError(
                    f"Relationship references unknown node '{rel_def.to_node}'. "
                    f"Available nodes: {node_labels}"
                )

