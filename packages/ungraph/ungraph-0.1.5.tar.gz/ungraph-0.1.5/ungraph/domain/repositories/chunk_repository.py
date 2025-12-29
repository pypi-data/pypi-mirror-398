"""
Interfaz de Repositorio: ChunkRepository

Una interfaz (o clase abstracta) define QUÉ operaciones necesitamos,
sin especificar CÓMO se implementan.

En Clean Architecture:
- Las interfaces están en el DOMINIO (no en infrastructure)
- El dominio define QUÉ necesita, no CÓMO se hace
- Las implementaciones concretas (Neo4j, PostgreSQL) van en infrastructure
- Esto permite cambiar la implementación sin tocar el código que la usa

Ejemplo de uso:
    # En application/use_cases/ingest_document.py
    class IngestDocumentUseCase:
        def __init__(self, repository: ChunkRepository):  # ← Usa la interfaz
            self.repository = repository
        
        def execute(self, chunk: Chunk):
            self.repository.save(chunk)  # No sabe si es Neo4j o PostgreSQL
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ungraph.domain.entities.chunk import Chunk


class ChunkRepository(ABC):
    """
    Interfaz que define las operaciones de persistencia para Chunks.
    
    Esta es una ABSTRACCIÓN: define el contrato que deben cumplir
    todas las implementaciones (Neo4j, PostgreSQL, archivo JSON, etc.)
    
    Regla importante: Esta interfaz está en el DOMINIO porque el dominio
    necesita definir QUÉ operaciones requiere, independientemente de
    cómo se implementen.
    """
    
    @abstractmethod
    def save(self, chunk: Chunk) -> None:
        """
        Guarda un chunk individual.
        
        Args:
            chunk: La entidad Chunk a guardar
            
        Raises:
            RepositoryError: Si ocurre un error al guardar
        """
        pass
    
    @abstractmethod
    def save_batch(self, chunks: List[Chunk]) -> None:
        """
        Guarda múltiples chunks de forma eficiente.
        
        Args:
            chunks: Lista de entidades Chunk a guardar
            
        Raises:
            RepositoryError: Si ocurre un error al guardar
        """
        pass
    
    @abstractmethod
    def find_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """
        Busca un chunk por su ID.
        
        Args:
            chunk_id: Identificador único del chunk
            
        Returns:
            La entidad Chunk si se encuentra, None si no existe
        """
        pass
    
    @abstractmethod
    def find_by_filename(self, filename: str) -> List[Chunk]:
        """
        Busca todos los chunks de un archivo específico.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Lista de entidades Chunk del archivo
        """
        pass
    
    @abstractmethod
    def create_chunk_relationships(self) -> None:
        """
        Crea relaciones entre chunks consecutivos.
        
        Esto es específico del dominio: necesitamos relaciones NEXT_CHUNK
        entre chunks consecutivos. La implementación puede variar
        (Neo4j usa relaciones, PostgreSQL usa foreign keys, etc.)
        """
        pass


