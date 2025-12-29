"""
Value Object: Provenance

Representa información de trazabilidad PROV-O básica.
Un value object es inmutable y se compara por valor, no por identidad.

En Clean Architecture, los value objects:
- Son inmutables
- Se comparan por valor (igualdad de atributos)
- NO tienen identidad propia
- Contienen validaciones de negocio

Ejemplo de uso:
    provenance = Provenance(
        was_derived_from="chunk_123",
        timestamp="2025-12-25T10:00:00Z",
        model_used="spacy_en_core_web_sm"
    )
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Provenance:
    """
    Value Object que representa información de trazabilidad PROV-O.
    
    Siguiendo el estándar PROV-O de W3C, este objeto registra:
    - wasDerivedFrom: Referencia a la entidad origen (chunk)
    - Timestamp de cuando se ejecutó la inferencia
    - Modelo/agente usado para la inferencia
    
    Attributes:
        was_derived_from: ID del chunk origen (prov:wasDerivedFrom)
        timestamp: Timestamp ISO 8601 de cuando se ejecutó la inferencia
        model_used: Nombre del modelo usado (ej: "spacy_en_core_web_sm")
        parameters: Parámetros del modelo (opcional, dict serializable)
    """
    was_derived_from: str
    timestamp: str
    model_used: str
    parameters: Optional[dict] = None
    
    def __post_init__(self):
        """
        Validaciones básicas después de crear la instancia.
        """
        if not self.was_derived_from:
            raise ValueError("was_derived_from cannot be empty")
        if not self.timestamp:
            raise ValueError("timestamp cannot be empty")
        if not self.model_used:
            raise ValueError("model_used cannot be empty")
        
        # Validar formato de timestamp (ISO 8601 básico)
        try:
            datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {self.timestamp}")
    
    @classmethod
    def create(
        cls,
        was_derived_from: str,
        model_used: str,
        parameters: Optional[dict] = None
    ) -> "Provenance":
        """
        Factory method para crear Provenance con timestamp actual.
        
        Args:
            was_derived_from: ID del chunk origen
            model_used: Nombre del modelo usado
            parameters: Parámetros del modelo (opcional)
        
        Returns:
            Provenance con timestamp actual en formato ISO 8601
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        return cls(
            was_derived_from=was_derived_from,
            timestamp=timestamp,
            model_used=model_used,
            parameters=parameters
        )




