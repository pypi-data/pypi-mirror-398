"""
Composition Root: Dependencies

Factory para crear y configurar todas las dependencias.
Este es el único lugar donde se crean implementaciones concretas.
"""

from pathlib import Path
from typing import Optional

from application.use_cases.ingest_document import IngestDocumentUseCase
from core.configuration import Settings

# Domain - Interfaces
from domain.services.inference_service import InferenceService

# Infrastructure - Implementaciones concretas
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository
from infrastructure.services.langchain_document_loader_service import LangChainDocumentLoaderService
from infrastructure.services.simple_text_cleaning_service import SimpleTextCleaningService
from infrastructure.services.langchain_chunking_service import LangChainChunkingService
from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
from infrastructure.services.neo4j_index_service import Neo4jIndexService
from infrastructure.services.spacy_inference_service import SpacyInferenceService


def create_inference_service(
    settings: Optional[Settings] = None,
    language: str = "en",
) -> Optional[InferenceService]:
    """
    Factory: crea y configura el servicio de inferencia.
    
    Creates appropriate inference service based on configuration:
    - inference_mode="ner": SpacyInferenceService (NER-based, default)
    - inference_mode="llm": LLMInferenceService (LLM-based, experimental)
    - inference_mode="hybrid": NotImplementedError (planned for v0.2.0)
    
    Args:
        settings: Configuration settings. If None, loads from environment.
        language: Language code for spaCy models ("en" or "es"). Only used for NER mode.
        
    Returns:
        InferenceService implementation or None if inference disabled
        
    Raises:
        ImportError: If required dependencies not installed
        NotImplementedError: If inference_mode="hybrid"
        ValueError: If inference_mode invalid
        
    Example:
        >>> settings = Settings(inference_mode="llm", ollama_base_url="http://localhost:11434")
        >>> service = create_inference_service(settings)
        >>> type(service).__name__
        'LLMInferenceService'
    """
    if settings is None:
        settings = Settings()
    
    inference_mode = settings.inference_mode.lower()
    
    # NER mode (default, existing implementation)
    if inference_mode == "ner":
        # Seleccionar modelo según idioma
        model_name = "en_core_web_sm" if language == "en" else "es_core_news_sm"
        
        try:
            return SpacyInferenceService(model_name=model_name)
        except ImportError as e:
            # Si spaCy no está instalado, retornar None
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"spaCy no está disponible. Fase Inference deshabilitada. "
                f"Instala con: pip install ungraph[infer] && python -m spacy download {model_name}"
            )
            return None
        except OSError as e:
            # Si el modelo no está disponible, sugerir instalación
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Modelo spaCy '{model_name}' no encontrado. "
                f"Instala con: python -m spacy download {model_name}"
            )
            return None
    
    # LLM mode (new, experimental)
    elif inference_mode == "llm":
        try:
            from langchain_community.chat_models import ChatOllama
            from infrastructure.services.llm_inference_service import LLMInferenceService
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Cannot load LLMInferenceService: {e}. "
                "Ensure langchain-experimental and langchain-community are installed."
            )
            return None
        
        # Validate Ollama configuration
        if not settings.ollama_model:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "LLM inference mode requires UNGRAPH_OLLAMA_MODEL to be set. "
                "Example: export UNGRAPH_OLLAMA_MODEL=llama3.2"
            )
            return None
        
        # Create LLM instance (Ollama default for v0.1.0)
        llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,  # Deterministic for entity extraction
        )
        
        # Default schema (general-purpose)
        allowed_nodes = [
            "Person",
            "Organization",
            "Location",
            "Product",
            "Event",
            "Concept",
        ]
        allowed_relationships = [
            "WORKS_FOR",
            "LOCATED_IN",
            "PART_OF",
            "RELATED_TO",
            "PRODUCED_BY",
        ]
        
        return LLMInferenceService(
            llm=llm,
            allowed_nodes=allowed_nodes,
            allowed_relationships=allowed_relationships,
            strict_mode=True,
        )
    
    # Hybrid mode (planned for v0.2.0)
    elif inference_mode == "hybrid":
        raise NotImplementedError(
            "Hybrid inference mode (NER + LLM) is planned for v0.2.0. "
            "Use 'ner' or 'llm' mode for now."
        )
    
    # Invalid mode
    else:
        raise ValueError(
            f"Invalid inference_mode: '{inference_mode}'. "
            "Valid options: 'ner', 'llm', 'hybrid'"
        )


def create_ingest_document_use_case(
    settings: Optional[Settings] = None,
    database: str = "neo4j",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    inference_language: str = "en"
) -> IngestDocumentUseCase:
    """
    Factory: crea y configura el caso de uso IngestDocumentUseCase.
    
    Este método:
    - Crea todas las implementaciones concretas
    - Configura las dependencias
    - Retorna el caso de uso listo para usar
    
    Args:
        settings: Configuration settings. If None, loads from environment.
        database: Nombre de la base de datos Neo4j (default: "neo4j")
        embedding_model: Modelo de embeddings a usar (default: all-MiniLM-L6-v2)
        inference_language: Idioma para inferencia ('en' para inglés, 'es' para español) (default: "en")
    
    Note:
        Inference mode is determined by settings.inference_mode:
        - "ner": SpaCy NER-based (default)
        - "llm": LLM-based (experimental, requires Ollama)
        - "hybrid": Planned for v0.2.0
    
    Returns:
        IngestDocumentUseCase configurado y listo para usar
    
    Note:
        Si inference service no puede crearse (dependencias faltantes),
        el pipeline funcionará sin fase Inference (solo ET).
    """
    if settings is None:
        settings = Settings()
    
    # Crear servicios de infraestructura
    text_cleaning_service = SimpleTextCleaningService()
    
    document_loader_service = LangChainDocumentLoaderService(
        text_cleaning_service=text_cleaning_service
    )
    
    chunking_service = LangChainChunkingService()
    
    embedding_service = HuggingFaceEmbeddingService(
        model_name=embedding_model
    )
    
    index_service = Neo4jIndexService(database=database)
    
    # Crear repositorio
    chunk_repository = Neo4jChunkRepository(database=database)
    
    # Crear servicio de inferencia basado en settings
    inference_service = create_inference_service(
        settings=settings,
        language=inference_language
    )
    
    # Crear caso de uso con dependencias inyectadas
    return IngestDocumentUseCase(
        document_loader_service=document_loader_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        index_service=index_service,
        chunk_repository=chunk_repository,
        inference_service=inference_service
    )

