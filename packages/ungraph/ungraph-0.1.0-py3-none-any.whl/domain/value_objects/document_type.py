"""
Value Object: DocumentType

Tipo de documento soportado por el sistema.
Es un Enum inmutable que representa los tipos de archivos que se pueden procesar.
"""

from enum import Enum


class DocumentType(Enum):
    """Tipos de documentos soportados - Value Object inmutable"""
    MARKDOWN = "markdown"
    TXT = "txt"
    WORD = "word"
    DOCX = "docx"
    PDF = "pdf"
    
    @classmethod
    def from_filename(cls, filename: str) -> "DocumentType":
        """
        Detecta el tipo de documento basándose en la extensión del archivo.
        
        Args:
            filename: Nombre del archivo con extensión
        
        Returns:
            DocumentType correspondiente
        
        Raises:
            ValueError: Si la extensión no es reconocida
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith(('.md', '.markdown')):
            return cls.MARKDOWN
        elif filename_lower.endswith('.txt'):
            return cls.TXT
        elif filename_lower.endswith(('.doc', '.docx')):
            return cls.DOCX if filename_lower.endswith('.docx') else cls.WORD
        elif filename_lower.endswith('.pdf'):
            return cls.PDF
        else:
            raise ValueError(f"Tipo de archivo no reconocido: {filename}")

