"""
Entidad de Dominio: Document

Representa el contenido extraído de un File físico.
En Clean Architecture, las entidades:
- Contienen SOLO datos (atributos)
- Pueden tener lógica de negocio básica (validaciones)
- NO conocen frameworks externos
- NO saben cómo cargarse o persistirse

Ejemplo de uso:
    document = Document(
        id="doc_123",
        content="Este es el contenido del documento",
        filename="example.md",
        file_type="markdown",
        metadata={"encoding": "utf-8", "file_path": "/path/to/file.md"}
    )
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid


@dataclass
class Document:
    """
    Entidad que representa el contenido extraído de un archivo físico.
    
    Attributes:
        id: Identificador único del documento
        content: Contenido textual extraído del archivo
        filename: Nombre del archivo original
        file_type: Tipo de archivo ('markdown', 'txt', 'word', 'docx')
        metadata: Metadatos adicionales (encoding, file_path, etc.)
    """
    id: str
    content: str
    filename: str
    file_type: str
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """
        Validaciones básicas de negocio después de crear la instancia.
        """
        if not self.id:
            raise ValueError("Document id cannot be empty")
        if not self.content:
            raise ValueError("Document content cannot be empty")
        if not self.filename:
            raise ValueError("Document filename cannot be empty")
        if not self.file_type:
            raise ValueError("Document file_type cannot be empty")
    
    @classmethod
    def create(
        cls,
        content: str,
        filename: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Document":
        """
        Factory method para crear un Document con ID generado automáticamente.
        
        Args:
            content: Contenido textual del documento
            filename: Nombre del archivo
            file_type: Tipo de archivo
            metadata: Metadatos adicionales (opcional)
        
        Returns:
            Document con ID generado automáticamente
        """
        return cls(
            id=f"{filename}_{uuid.uuid4()}",
            content=content,
            filename=filename,
            file_type=file_type,
            metadata=metadata or {}
        )
    
    def get_encoding(self) -> Optional[str]:
        """
        Método de dominio: extrae el encoding de los metadatos.
        """
        return self.metadata.get('encoding')
    
    def get_file_path(self) -> Optional[str]:
        """
        Método de dominio: extrae el file_path de los metadatos.
        """
        return self.metadata.get('file_path')
