"""
Interfaz de Servicio: EmbeddingService

Define las operaciones para generar embeddings de texto.
"""

from abc import ABC, abstractmethod
from typing import List
from domain.entities.chunk import Chunk
from domain.value_objects.embedding import Embedding


class EmbeddingService(ABC):
    """
    Interfaz que define las operaciones para generar embeddings.
    
    Las implementaciones pueden usar diferentes modelos:
    - HuggingFace (sentence-transformers)
    - Ollama
    - OpenAI
    - etc.
    """
    
    @abstractmethod
    def generate_embedding(self, text: str) -> Embedding:
        """
        Genera un embedding para un texto.
        
        Args:
            text: Texto a convertir en embedding
        
        Returns:
            Value Object Embedding con el vector y metadatos
        
        Raises:
            ValueError: Si el texto está vacío
        """
        pass
    
    @abstractmethod
    def generate_embeddings_batch(self, chunks: List[Chunk]) -> List[Embedding]:
        """
        Genera embeddings para múltiples chunks de forma eficiente.
        
        Args:
            chunks: Lista de entidades Chunk
        
        Returns:
            Lista de Value Objects Embedding en el mismo orden que los chunks
        
        Raises:
            ValueError: Si la lista de chunks está vacía
        """
        pass

