"""
Implementación: HuggingFaceEmbeddingService

Implementa EmbeddingService usando HuggingFace sentence-transformers.
Envuelve el código existente del notebook.
"""

import logging
from typing import List
import torch

from domain.services.embedding_service import EmbeddingService
from domain.entities.chunk import Chunk
from domain.value_objects.embedding import Embedding

# LangChain puede estar deprecado, pero usamos lo que existe
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingService(EmbeddingService):
    """
    Implementación de EmbeddingService usando HuggingFace.
    
    Usa sentence-transformers/all-MiniLM-L6-v2 por defecto (384 dimensiones).
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Inicializa el servicio de embeddings.
        
        Args:
            model_name: Nombre del modelo de HuggingFace (default: all-MiniLM-L6-v2)
        """
        self.model_name = model_name
        
        # Detectar dispositivo
        if torch.cuda.is_available():
            device = 'cuda'
            logger.info("CUDA disponible, usando GPU para embeddings.")
        else:
            device = 'cpu'
            logger.info("CUDA no disponible, usando CPU para embeddings.")
        
        model_kwargs = {'device': device}
        encode_kwargs = {'normalize_embeddings': False}
        
        self.encoder = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        
        # Detectar dimensiones (384 para all-MiniLM-L6-v2)
        self.dimensions = 384  # Valor conocido para el modelo por defecto
        logger.info(f"Embedding service initialized with model: {model_name}")
    
    def generate_embedding(self, text: str) -> Embedding:
        """
        Genera un embedding para un texto.
        
        Basado en create_document_object del notebook.
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Generar embedding
        vector = self.encoder.embed_query(text)
        
        # Convertir a lista de floats
        vector_list = [float(x) for x in vector]
        
        return Embedding(
            vector=vector_list,
            dimensions=self.dimensions,
            encoder_info=str(self.encoder)
        )
    
    def generate_embeddings_batch(self, chunks: List[Chunk]) -> List[Embedding]:
        """
        Genera embeddings para múltiples chunks.
        
        Basado en create_document_object del notebook.
        """
        if not chunks:
            raise ValueError("Chunks list cannot be empty")
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        embeddings = []
        for chunk in chunks:
            embedding = self.generate_embedding(chunk.page_content)
            embeddings.append(embedding)
        
        logger.info(f"Embeddings generation completed")
        return embeddings

