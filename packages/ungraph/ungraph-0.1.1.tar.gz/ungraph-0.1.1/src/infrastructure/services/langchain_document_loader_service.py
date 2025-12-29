"""
Implementación: LangChainDocumentLoaderService

Implementa DocumentLoaderService usando LangChain.
Envuelve el código existente del notebook.
"""

from typing import List
from pathlib import Path
import logging

from domain.services.document_loader_service import DocumentLoaderService
from domain.entities.document import Document
from domain.value_objects.document_type import DocumentType

# Imports de LangChain (infrastructure puede usar frameworks)
from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
    TextLoader
)

# Importar Docling para PDFs (opcional, puede no estar instalado)
try:
    from langchain_docling import DoclingLoader
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Importar función de detección de encoding
from src.utils.handlers import detect_encoding

logger = logging.getLogger(__name__)


class LangChainDocumentLoaderService(DocumentLoaderService):
    """
    Implementación de DocumentLoaderService usando LangChain.
    
    Soporta:
    - Markdown (.md, .markdown)
    - Texto plano (.txt)
    - Word (.doc, .docx)
    - PDF (.pdf) usando langchain-docling (IBM Docling)
    """
    
    def __init__(self, text_cleaning_service=None):
        """
        Inicializa el servicio.
        
        Args:
            text_cleaning_service: Servicio opcional para limpiar texto
        """
        self.text_cleaning_service = text_cleaning_service
    
    def supports(self, file_path: Path) -> bool:
        """Verifica si puede cargar el tipo de archivo."""
        suffix = file_path.suffix.lower()
        supported = ['.md', '.markdown', '.txt', '.doc', '.docx']
        if DOCLING_AVAILABLE:
            supported.append('.pdf')
        return suffix in supported
    
    def load(self, file_path: Path, clean: bool = True) -> List[Document]:
        """
        Carga un archivo y lo convierte en Document(s).
        
        Usa el código del notebook adaptado a nuestras entidades.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        # Cargar según el tipo de archivo
        if suffix in ['.md', '.markdown']:
            return self._load_markdown(file_path, clean)
        elif suffix == '.txt':
            return self._load_txt(file_path, clean)
        elif suffix in ['.doc', '.docx']:
            return self._load_word(file_path, clean)
        elif suffix == '.pdf':
            return self._load_pdf(file_path, clean)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {suffix}")
    
    def _load_markdown(self, file_path: Path, clean: bool) -> List[Document]:
        """Carga un archivo Markdown."""
        logger.info(f"Cargando archivo Markdown: {file_path}")
        
        loader = UnstructuredMarkdownLoader(str(file_path))
        langchain_docs = loader.load()
        
        documents = []
        for lc_doc in langchain_docs:
            content = lc_doc.page_content
            
            # Limpiar si está habilitado
            if clean and self.text_cleaning_service:
                content = self.text_cleaning_service.clean(content)
            
            # Crear entidad Document del dominio
            doc = Document.create(
                content=content,
                filename=file_path.name,
                file_type=DocumentType.MARKDOWN.value,
                metadata={
                    'file_path': str(file_path),
                    **lc_doc.metadata
                }
            )
            documents.append(doc)
        
        logger.info(f"Archivo cargado exitosamente. Documentos generados: {len(documents)}")
        return documents
    
    def _load_txt(self, file_path: Path, clean: bool) -> List[Document]:
        """
        Carga un archivo de texto con detección automática de codificación.
        
        Usa detect_encoding para detectar la codificación automáticamente,
        con fallback a codificaciones comunes si falla.
        """
        logger.info(f"Cargando archivo de texto: {file_path}")
        
        # Detectar encoding automáticamente
        encoding = detect_encoding(file_path)
        logger.info(f"Codificación detectada: {encoding}")
        
        # Lista de codificaciones de fallback si la detectada falla
        fallback_encodings = ['windows-1252', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
        
        # Intentar cargar con la codificación detectada
        last_error = None
        langchain_docs = None
        
        # Probar primero con la codificación detectada
        try:
            loader = TextLoader(str(file_path), encoding=encoding)
            langchain_docs = loader.load()
            logger.info(f"Archivo cargado exitosamente con codificación: {encoding}")
        except (UnicodeDecodeError, RuntimeError) as e:
            last_error = e
            logger.warning(f"Error al cargar con codificación detectada {encoding}: {e}")
            
            # Intentar con codificaciones de fallback
            logger.info("Intentando con codificaciones de fallback...")
            for fallback_enc in fallback_encodings:
                if fallback_enc == encoding:
                    continue  # Ya probamos esta
                try:
                    logger.info(f"Intentando con codificación: {fallback_enc}")
                    loader = TextLoader(str(file_path), encoding=fallback_enc)
                    langchain_docs = loader.load()
                    encoding = fallback_enc  # Actualizar la codificación usada
                    logger.info(f"Archivo cargado exitosamente con codificación: {encoding}")
                    break
                except (UnicodeDecodeError, RuntimeError) as e:
                    last_error = e
                    continue
            
            # Si todas las codificaciones fallan, lanzar error
            if langchain_docs is None:
                raise RuntimeError(
                    f"No se pudo cargar el archivo {file_path} con ninguna codificación. "
                    f"Último error: {last_error}"
                ) from last_error
        
        documents = []
        for lc_doc in langchain_docs:
            content = lc_doc.page_content
            
            # Limpiar si está habilitado
            if clean and self.text_cleaning_service:
                content = self.text_cleaning_service.clean(content)
            
            # Crear entidad Document del dominio
            doc = Document.create(
                content=content,
                filename=file_path.name,
                file_type=DocumentType.TXT.value,
                metadata={
                    'file_path': str(file_path),
                    'encoding': encoding,
                    **lc_doc.metadata
                }
            )
            documents.append(doc)
        
        logger.info(f"Archivo cargado exitosamente. Documentos generados: {len(documents)}")
        return documents
    
    def _load_word(self, file_path: Path, clean: bool) -> List[Document]:
        """Carga un archivo Word."""
        logger.info(f"Cargando archivo Word: {file_path}")
        
        loader = UnstructuredWordDocumentLoader(str(file_path))
        langchain_docs = loader.load()
        
        documents = []
        for lc_doc in langchain_docs:
            content = lc_doc.page_content
            
            # Limpiar si está habilitado
            if clean and self.text_cleaning_service:
                content = self.text_cleaning_service.clean(content)
            
            # Crear entidad Document del dominio
            doc = Document.create(
                content=content,
                filename=file_path.name,
                file_type=DocumentType.DOCX.value,
                metadata={
                    'file_path': str(file_path),
                    **lc_doc.metadata
                }
            )
            documents.append(doc)
        
        logger.info(f"Archivo cargado exitosamente. Documentos generados: {len(documents)}")
        return documents
    
    def _load_pdf(self, file_path: Path, clean: bool) -> List[Document]:
        """
        Carga un archivo PDF usando langchain-docling (IBM Docling).
        
        Docling proporciona mejor extracción de texto y metadatos que otros loaders,
        incluyendo información sobre estructura del documento, tablas, imágenes, etc.
        
        Args:
            file_path: Ruta al archivo PDF
            clean: Si True, limpia el texto antes de procesar
        
        Returns:
            Lista de Document entities
        
        Raises:
            ImportError: Si langchain-docling no está instalado
            RuntimeError: Si hay un error al cargar el PDF
        """
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "langchain-docling no está instalado. "
                "Instala con: pip install langchain-docling"
            )
        
        logger.info(f"Cargando archivo PDF con Docling: {file_path}")
        
        try:
            # DoclingLoader puede tomar parámetros opcionales para configuración
            loader = DoclingLoader(str(file_path))
            langchain_docs = loader.load()
            
            documents = []
            for lc_doc in langchain_docs:
                content = lc_doc.page_content
                
                # Limpiar si está habilitado
                if clean and self.text_cleaning_service:
                    content = self.text_cleaning_service.clean(content)
                
                # Extraer metadatos de Docling (puede incluir información de estructura)
                metadata = {
                    'file_path': str(file_path),
                    'file_type': 'pdf',
                    **lc_doc.metadata
                }
                
                # Docling puede proporcionar metadatos adicionales como:
                # - page_number: número de página
                # - document_structure: información sobre estructura del documento
                # - tables: información sobre tablas extraídas
                # - images: información sobre imágenes
                
                # Crear entidad Document del dominio
                doc = Document.create(
                    content=content,
                    filename=file_path.name,
                    file_type=DocumentType.PDF.value,
                    metadata=metadata
                )
                documents.append(doc)
            
            logger.info(
                f"PDF cargado exitosamente con Docling. "
                f"Documentos generados: {len(documents)}"
            )
            return documents
            
        except Exception as e:
            logger.error(f"Error al cargar PDF con Docling: {e}", exc_info=True)
            raise RuntimeError(f"Error al cargar PDF {file_path}: {e}") from e

