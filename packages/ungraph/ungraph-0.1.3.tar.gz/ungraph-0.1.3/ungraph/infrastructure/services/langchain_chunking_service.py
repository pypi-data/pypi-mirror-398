"""
Implementación: LangChainChunkingService

Implementa ChunkingService usando LangChain RecursiveCharacterTextSplitter.
"""

import logging
from typing import List
import uuid

from domain.services.chunking_service import ChunkingService
from domain.entities.document import Document
from domain.entities.chunk import Chunk
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class LangChainChunkingService(ChunkingService):
    """
    Implementación de ChunkingService usando LangChain.
    
    Usa RecursiveCharacterTextSplitter para dividir documentos.
    """
    
    def chunk(
        self,
        document: Document,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Chunk]:
        """
        Divide un documento en chunks usando RecursiveCharacterTextSplitter.
        
        Basado en el código del notebook.
        """
        logger.info(f"Chunking document: {document.filename}")
        
        # Crear splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Dividir el contenido
        texts = text_splitter.split_text(document.content)
        
        # Convertir a entidades Chunk del dominio
        chunks = []
        for i, text in enumerate(texts, start=1):
            chunk = Chunk(
                id=f"{document.filename}_{uuid.uuid4()}",
                page_content=text,
                metadata={
                    'filename': document.filename,
                    'file_type': document.file_type,
                    **document.metadata
                },
                chunk_id_consecutive=i
            )
            chunks.append(chunk)
        
        logger.info(f"Document divided into {len(chunks)} chunks")
        return chunks

    def smart_chunk(
        self,
        document: Document,
        preferred_strategy: str | None = None,
        evaluate_all: bool = False,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None
    ) -> tuple[list[Chunk], dict]:
        """
        Chunking inteligente: usa `master_chunking_function` para seleccionar la mejor
        estrategia (fixed/lexical/semantic/hierarchical) y devolver chunks con metadata.

        Returns:
            (chunks, metadata)
        """
        logger.info(f"Smart chunking document: {document.filename} (preferred={preferred_strategy})")

        # Import here to avoid heavy import at module load
        try:
            from langchain_core.documents import Document as LC_Doc
            from ...utils.chunking_master import master_chunking_function
        except Exception as e:
            logger.error(f"Chunking master not available: {e}")
            raise

        # Convertir a LangChain Document
        lc_doc = LC_Doc(page_content=document.content, metadata={**document.metadata, 'filename': document.filename, 'file_type': document.file_type})

        chunks_docs, metadata = master_chunking_function(
            documents=[lc_doc],
            file_path=document.metadata.get('file_path'),
            embedding_model=None,
            model_max_tokens=None,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            preferred_strategy=preferred_strategy,
            evaluate_all=evaluate_all
        )

        # Convertir los langchain docs a domain Chunk
        domain_chunks: list[Chunk] = []
        for i, lc in enumerate(chunks_docs, start=1):
            # lc may be a langchain Document or a dict-like
            content = getattr(lc, 'page_content', None) or getattr(lc, 'content', None) or str(lc)
            md = getattr(lc, 'metadata', {}) or {}
            chunk = Chunk(
                id=f"{document.filename}_{uuid.uuid4()}",
                page_content=content,
                metadata={
                    'filename': document.filename,
                    **md
                },
                chunk_id_consecutive=i
            )
            domain_chunks.append(chunk)

        return domain_chunks, metadata

