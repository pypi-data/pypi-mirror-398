"""
Interfaz de Servicio: DocumentLoaderService

Define las operaciones para cargar archivos y convertirlos en Document.
Las implementaciones pueden usar LangChain, Docling, u otras librerías.
"""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from ungraph.domain.entities.document import Document


class DocumentLoaderService(ABC):
    """
    Interfaz que define las operaciones para cargar documentos desde archivos.
    
    Las implementaciones pueden cargar diferentes tipos de archivos:
    - Markdown (.md, .markdown)
    - Texto plano (.txt)
    - Word (.doc, .docx)
    - PDF (.pdf) usando langchain-docling (IBM Docling)
    - Audio (.mp3, .wav, .ogg) (futuro - lejano)
    - Video (.mp4, .avi, .mkv) (futuro - lejano)
    - Imagen (.jpg, .png, .gif) (futuro)
    - Spreadsheet (.xls, .xlsx, .csv) (futuro - proximo)
    - Presentación (.ppt, .pptx) (futuro- lejano)
    - Código (.py, .js, .html) (futuro - proximo)
    
    """
    
    @abstractmethod
    def load(self, file_path: Path, clean: bool = True) -> List[Document]:
        """
        Carga un archivo y lo convierte en uno o más Document(s).
        
        Args:
            file_path: Ruta al archivo a cargar
            clean: Si True, aplica limpieza de texto (default: True)
        
        Returns:
            Lista de entidades Document con el contenido del archivo
        
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no puede ser procesado
        """
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """
        Verifica si este servicio puede cargar el tipo de archivo especificado.
        
        Args:
            file_path: Ruta al archivo
        
        Returns:
            True si el servicio puede cargar el archivo, False en caso contrario
        """
        pass

