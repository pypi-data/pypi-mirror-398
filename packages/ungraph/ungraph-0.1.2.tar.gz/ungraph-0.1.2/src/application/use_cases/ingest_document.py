"""
Caso de Uso: IngestDocumentUseCase

Orquesta el flujo completo de ingestión de documentos siguiendo el patrón ETI:
1. Extract: Cargar documento desde archivo
2. Transform: Dividir en chunks, generar embeddings
3. Inference: Extraer entidades, relaciones y facts (opcional)
4. Persistir en el grafo
5. Crear relaciones entre chunks
"""

import logging
from pathlib import Path
from typing import List, Optional

from domain.entities.document import Document
from domain.entities.chunk import Chunk
from domain.entities.fact import Fact
from domain.services.document_loader_service import DocumentLoaderService
from domain.services.chunking_service import ChunkingService
from domain.services.embedding_service import EmbeddingService
from domain.services.index_service import IndexService
from domain.services.inference_service import InferenceService
from domain.repositories.chunk_repository import ChunkRepository
from domain.value_objects.graph_pattern import GraphPattern

logger = logging.getLogger(__name__)


class IngestDocumentUseCase:
    """
    Caso de uso para ingerir un documento completo al grafo de conocimiento.
    
    Este caso de uso:
    - Depende SOLO de interfaces del dominio (no de implementaciones concretas)
    - Orquesta el flujo completo de ingestión
    - Es fácil de testear (puedes mockear las dependencias)
    """
    
    def __init__(
        self,
        document_loader_service: DocumentLoaderService,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        index_service: IndexService,
        chunk_repository: ChunkRepository,
        inference_service: Optional[InferenceService] = None
    ):
        """
        Inicializa el caso de uso con sus dependencias.
        
        Args:
            document_loader_service: Servicio para cargar documentos
            chunking_service: Servicio para dividir documentos
            embedding_service: Servicio para generar embeddings
            index_service: Servicio para crear índices
            chunk_repository: Repositorio para persistir chunks
            inference_service: Servicio de inferencia (opcional). Si se proporciona,
                              se ejecuta la fase Inference del patrón ETI.
        """
        self.document_loader_service = document_loader_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.index_service = index_service
        self.chunk_repository = chunk_repository
        self.inference_service = inference_service
    
    def execute(
        self,
        file_path: Path,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        clean_text: bool = True,
        pattern: Optional[GraphPattern] = None
    ) -> List[Chunk]:
        """
        Ejecuta el caso de uso completo siguiendo el patrón ETI.
        
        Flujo ETI:
        1. Extract: Cargar documento desde archivo
        2. Transform: Dividir en chunks, generar embeddings
        3. Inference: Extraer entidades, relaciones y facts (si inference_service está disponible)
        4. Persistir chunks y facts en el grafo (usando patrón si se proporciona)
        5. Crear relaciones entre chunks consecutivos
        
        Args:
            file_path: Ruta al archivo a ingerir
            chunk_size: Tamaño de cada chunk (default: 1000)
            chunk_overlap: Overlap entre chunks (default: 200)
            clean_text: Si True, limpia el texto (default: True)
            pattern: Patrón de grafo opcional. Si es None, usa FILE_PAGE_CHUNK (comportamiento por defecto)
        
        Returns:
            Lista de Chunks creados
        
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no puede ser procesado
        
        Note:
            Si se proporciona un patrón personalizado, debe ser compatible con la estructura de Chunk.
            El patrón FILE_PAGE_CHUNK es el patrón por defecto y está completamente soportado.
            La fase Inference solo se ejecuta si inference_service está configurado.
        """
        logger.info(f"Starting document ingestion: {file_path}")
        
        # Si no se proporciona patrón, usar FILE_PAGE_CHUNK (comportamiento por defecto)
        if pattern is None:
            from domain.value_objects.predefined_patterns import FILE_PAGE_CHUNK_PATTERN
            pattern = FILE_PAGE_CHUNK_PATTERN
        
        logger.info(f"Using pattern: {pattern.name}")
        
        # 1. Cargar documento
        logger.info("Step 1: Loading document")
        documents = self.document_loader_service.load(file_path, clean=clean_text)
        
        if not documents:
            raise ValueError(f"No documents loaded from {file_path}")
        
        # Por ahora procesamos solo el primer documento
        # (en el futuro podríamos procesar múltiples documentos)
        document = documents[0]
        
        # 2. Dividir en chunks
        logger.info("Step 2: Chunking document")
        chunks = self.chunking_service.chunk(
            document,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        if not chunks:
            raise ValueError("No chunks generated from document")
        
        # 3. Generar embeddings
        logger.info("Step 3: Generating embeddings")
        embeddings = self.embedding_service.generate_embeddings_batch(chunks)
        
        # Asignar embeddings a chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embeddings = embedding.vector
            chunk.embeddings_dimensions = embedding.dimensions
            chunk.embedding_encoder_info = embedding.encoder_info
        
        # 4. Inference: Extraer entidades, relaciones y facts (si está disponible)
        all_facts: List[Fact] = []
        if self.inference_service:
            logger.info("Step 4: Running inference phase (ETI)")
            for chunk in chunks:
                try:
                    chunk_facts = self.inference_service.infer_facts(chunk)
                    all_facts.extend(chunk_facts)
                    logger.debug(f"Inferred {len(chunk_facts)} facts from chunk {chunk.id}")
                except Exception as e:
                    logger.warning(f"Error inferring facts from chunk {chunk.id}: {e}")
                    # Continuar con otros chunks aunque uno falle
            logger.info(f"Inference phase completed. Generated {len(all_facts)} facts")
        else:
            logger.info("Step 4: Skipping inference phase (no inference_service provided)")
        
        # 5. Configurar índices
        logger.info("Step 5: Setting up indexes")
        self.index_service.setup_all_indexes()
        
        # 6. Persistir chunks usando el patrón especificado
        logger.info(f"Step 6: Persisting chunks with pattern {pattern.name}")
        # Verificar si el repositorio soporta save_with_pattern
        if hasattr(self.chunk_repository, 'save_with_pattern'):
            self.chunk_repository.save_with_pattern(chunks, pattern)
        else:
            # Fallback: usar save_batch si el repositorio no soporta patrones
            logger.warning("Repository does not support patterns, using save_batch()")
            self.chunk_repository.save_batch(chunks)
        
        # 7. Persistir facts si se generaron
        if all_facts and hasattr(self.chunk_repository, 'save_facts'):
            logger.info(f"Step 7: Persisting {len(all_facts)} facts")
            try:
                self.chunk_repository.save_facts(all_facts)
                logger.info(f"Successfully persisted {len(all_facts)} facts")
            except Exception as e:
                logger.error(f"Error persisting facts: {e}")
                # No fallar el proceso completo si falla la persistencia de facts
        elif all_facts:
            logger.warning("Facts generated but repository does not support save_facts()")
        
        # 8. Crear relaciones entre chunks consecutivos
        # Solo para FILE_PAGE_CHUNK por ahora
        if pattern.name == "FILE_PAGE_CHUNK":
            logger.info("Step 8: Creating chunk relationships")
            self.chunk_repository.create_chunk_relationships()
        else:
            logger.info(f"Skipping chunk relationships for pattern {pattern.name}")
        
        logger.info(
            f"Document ingestion completed. Created {len(chunks)} chunks"
            + (f" and {len(all_facts)} facts" if all_facts else "")
        )
        return chunks

