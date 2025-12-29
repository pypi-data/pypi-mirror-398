"""
Entidad de Dominio: Relation

Representa una relación entre dos entidades extraída de un chunk.

En Clean Architecture, las entidades:
- Contienen SOLO datos (atributos)
- Pueden tener lógica de negocio básica (validaciones)
- NO conocen frameworks externos
- NO saben cómo persistirse

Ejemplo de uso:
    relation = Relation(
        id="rel_123",
        source_entity_id="entity_1",
        target_entity_id="entity_2",
        relation_type="WORKS_FOR",
        confidence=0.85,
        provenance_ref="chunk_1"
    )
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Relation:
    """
    Entidad que representa una relación entre dos entidades.
    
    Una relación conecta dos entidades con un tipo específico de relación,
    extraída mediante inferencia desde un chunk de texto.
    
    Attributes:
        id: Identificador único de la relación
        source_entity_id: ID de la entidad origen
        target_entity_id: ID de la entidad destino
        relation_type: Tipo de relación (ej: "WORKS_FOR", "LOCATED_IN", etc.)
        confidence: Nivel de confianza (0.0-1.0)
        provenance_ref: Referencia al chunk origen (para trazabilidad PROV-O)
    """
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    confidence: float
    provenance_ref: str
    
    def __post_init__(self):
        """
        Validaciones básicas de negocio después de crear la instancia.
        """
        if not self.id:
            raise ValueError("Relation id cannot be empty")
        if not self.source_entity_id:
            raise ValueError("Relation source_entity_id cannot be empty")
        if not self.target_entity_id:
            raise ValueError("Relation target_entity_id cannot be empty")
        if not self.relation_type:
            raise ValueError("Relation relation_type cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not self.provenance_ref:
            raise ValueError("Relation provenance_ref cannot be empty")
        if self.source_entity_id == self.target_entity_id:
            raise ValueError("Source and target entity cannot be the same")
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """
        Método de dominio: verifica si la relación tiene alta confianza.
        
        Args:
            threshold: Umbral de confianza (default: 0.8)
        
        Returns:
            True si confidence >= threshold
        """
        return self.confidence >= threshold
    
    def to_triple(self) -> tuple[str, str, str]:
        """
        Método de dominio: convierte la relación a una tripleta.
        
        Returns:
            Tupla (source_entity_id, relation_type, target_entity_id)
        """
        return (self.source_entity_id, self.relation_type, self.target_entity_id)




