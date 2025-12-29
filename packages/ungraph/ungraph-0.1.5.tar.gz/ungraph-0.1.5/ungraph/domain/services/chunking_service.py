"""
Interfaz de Servicio: ChunkingService

Define las operaciones para dividir documentos en chunks.
"""

from abc import ABC, abstractmethod
from typing import List
from ungraph.domain.entities.document import Document
from ungraph.domain.entities.chunk import Chunk


class ChunkingService(ABC):
    """
    Interfaz que define las operaciones para dividir documentos en chunks.
    
    Las implementaciones pueden usar diferentes estrategias:
    - RecursiveCharacterTextSplitter
    - MarkdownHeaderTextSplitter
    - SemanticChunker
    - etc.
    """
    
    @abstractmethod
    def chunk(
        self,
        document: Document,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Chunk]:
        """
        Divide un documento en chunks.
        
        Args:
            document: Documento a dividir
            chunk_size: Tamaño de cada chunk en caracteres (default: 1000)
            chunk_overlap: Overlap entre chunks en caracteres (default: 200)
        
        Returns:
            Lista de entidades Chunk
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        pass

