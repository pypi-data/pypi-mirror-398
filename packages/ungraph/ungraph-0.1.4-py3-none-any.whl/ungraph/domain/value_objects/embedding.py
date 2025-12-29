"""
Value Object: Embedding

Representa un vector de embeddings con sus metadatos.
Es inmutable (frozen=True) porque los embeddings no deben cambiar una vez creados.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Embedding:
    """
    Value Object que representa un vector de embeddings.
    
    Attributes:
        vector: Lista de números flotantes que representan el embedding
        dimensions: Dimensión del vector (ej: 384 para all-MiniLM-L6-v2)
        encoder_info: Información del encoder usado para generar el embedding
    """
    vector: List[float]
    dimensions: int
    encoder_info: str
    
    def __post_init__(self):
        """
        Validaciones básicas del Value Object.
        """
        if not self.vector:
            raise ValueError("Embedding vector cannot be empty")
        if len(self.vector) != self.dimensions:
            raise ValueError(
                f"Vector dimension mismatch: "
                f"expected {self.dimensions}, got {len(self.vector)}"
            )
        if self.dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive")
        if not self.encoder_info:
            raise ValueError("Encoder info cannot be empty")

