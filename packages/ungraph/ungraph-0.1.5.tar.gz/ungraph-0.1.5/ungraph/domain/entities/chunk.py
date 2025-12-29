"""
Entidad de Dominio: Chunk

Una entidad representa un objeto de negocio con identidad propia.
En Clean Architecture, las entidades:
- Contienen SOLO datos (atributos)
- Pueden tener lógica de negocio básica (validaciones, cálculos)
- NO conocen frameworks externos (Neo4j, LangChain, etc.)
- NO saben cómo guardarse o persistirse (eso es responsabilidad del repositorio)

Ejemplo de uso:
    chunk = Chunk(
        id="chunk_123",
        page_content="Este es el contenido del chunk",
        metadata={"filename": "doc.md", "page": 1}
    )
    print(chunk.page_content)  # Acceder a datos
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class Chunk:
    """
    Entidad que representa un chunk de texto en el dominio.
    
    Attributes:
        id: Identificador único del chunk
        page_content: Contenido textual del chunk (nombre consistente con código existente)
        metadata: Metadatos adicionales (filename, page_number, etc.)
        chunk_id_consecutive: Número consecutivo del chunk en el documento
        embeddings: Vector de embeddings (opcional)
        embeddings_dimensions: Dimensión del vector de embeddings
        embedding_encoder_info: Información del encoder usado
        is_unitary: Indica si el chunk es unitario (no dividido)
    """
    id: str
    page_content: str
    metadata: Dict[str, Any]
    chunk_id_consecutive: Optional[int] = None
    embeddings: Optional[List[float]] = None
    embeddings_dimensions: Optional[int] = None
    embedding_encoder_info: Optional[str] = None
    is_unitary: bool = False
    
    def __post_init__(self):
        """
        Validaciones básicas de negocio después de crear la instancia.
        Esto es lógica de dominio permitida en entidades.
        """
        if not self.id:
            raise ValueError("Chunk id cannot be empty")
        if not self.page_content:
            raise ValueError("Chunk content cannot be empty")
        if self.embeddings and self.embeddings_dimensions:
            if len(self.embeddings) != self.embeddings_dimensions:
                raise ValueError(
                    f"Embeddings dimension mismatch: "
                    f"expected {self.embeddings_dimensions}, got {len(self.embeddings)}"
                )
    
    def get_filename(self) -> Optional[str]:
        """
        Método de dominio: extrae el filename de los metadatos.
        Esto es lógica de negocio, no persistencia.
        """
        return self.metadata.get('filename')
    
    def get_page_number(self) -> Optional[int]:
        """
        Método de dominio: extrae el número de página de los metadatos.
        """
        return self.metadata.get('page_number')
