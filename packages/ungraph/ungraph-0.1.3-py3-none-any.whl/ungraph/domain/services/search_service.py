"""
Interfaz de Servicio: SearchService

Define las operaciones para buscar en el grafo de conocimiento.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from domain.value_objects.embedding import Embedding


class SearchResult:
    """
    Resultado de una búsqueda en el grafo.
    
    Attributes:
        content: Contenido del chunk encontrado
        score: Score de relevancia (0.0 a 1.0)
        chunk_id: ID del chunk
        chunk_id_consecutive: Número consecutivo del chunk
        previous_chunk_content: Contenido del chunk anterior (opcional)
        next_chunk_content: Contenido del chunk siguiente (opcional)
    """
    def __init__(
        self,
        content: str,
        score: float,
        chunk_id: str,
        chunk_id_consecutive: int,
        previous_chunk_content: str = None,
        next_chunk_content: str = None
    ):
        self.content = content
        self.score = score
        self.chunk_id = chunk_id
        self.chunk_id_consecutive = chunk_id_consecutive
        self.previous_chunk_content = previous_chunk_content
        self.next_chunk_content = next_chunk_content


class SearchService(ABC):
    """
    Interfaz que define las operaciones para buscar en el grafo.
    
    Las implementaciones pueden usar diferentes estrategias:
    - Búsqueda por texto (full-text search)
    - Búsqueda vectorial (similarity search)
    - Búsqueda híbrida (combinación de ambas)
    """
    
    @abstractmethod
    def text_search(
        self,
        query_text: str,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Búsqueda por texto usando índice full-text.
        
        Args:
            query_text: Texto a buscar
            limit: Número máximo de resultados (default: 5)
        
        Returns:
            Lista de SearchResult ordenados por score descendente
        
        Raises:
            ValueError: Si el query_text está vacío
        """
        pass
    
    @abstractmethod
    def vector_search(
        self,
        query_embedding: Embedding,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Búsqueda vectorial usando embeddings.
        
        Args:
            query_embedding: Embedding de la consulta
            limit: Número máximo de resultados (default: 5)
        
        Returns:
            Lista de SearchResult ordenados por score descendente
        
        Raises:
            ValueError: Si el embedding es inválido
        """
        pass
    
    @abstractmethod
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: Embedding,
        weights: Tuple[float, float] = (0.3, 0.7),
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Búsqueda híbrida combinando texto y vectorial.
        
        Args:
            query_text: Texto a buscar
            query_embedding: Embedding de la consulta
            weights: Pesos para combinar scores (text_weight, vector_weight) (default: (0.3, 0.7))
            limit: Número máximo de resultados (default: 5)
        
        Returns:
            Lista de SearchResult ordenados por score combinado descendente
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        pass

