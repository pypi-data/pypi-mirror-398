"""
Módulo maestro para selección y evaluación de estrategias de chunking.

Este módulo proporciona una función maestra que analiza documentos y selecciona
la mejor estrategia de chunking basándose en características del contenido,
estructura del documento y métricas de calidad.

Autor: Sistema de chunking inteligente
Fecha: 2024
"""

import logging
import re
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
    PythonCodeTextSplitter,
    HTMLHeaderTextSplitter,
)
try:
    from langchain_text_splitters import Language, LanguageParser
except ImportError:
    # Fallback si LanguageParser no está disponible
    Language = None
    LanguageParser = None
try:
    from langchain_experimental.text_splitter import SemanticChunker  # type: ignore
except ImportError:
    SemanticChunker = None

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Tipos de documentos soportados."""
    MARKDOWN = "markdown"
    HTML = "html"
    PYTHON = "python"
    CODE = "code"
    NARRATIVE = "narrative"
    TECHNICAL = "technical"
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"


class ChunkingStrategy(Enum):
    """Estrategias de chunking disponibles."""
    CHARACTER = "character"
    RECURSIVE = "recursive"
    TOKEN = "token"
    MARKDOWN_HEADER = "markdown_header"
    HTML_HEADER = "html_header"
    PYTHON_CODE = "python_code"
    SEMANTIC = "semantic"
    LANGUAGE_SPECIFIC = "language_specific"


@dataclass
class ChunkingMetrics:
    """Métricas para evaluar la calidad del chunking."""
    num_chunks: int
    avg_chunk_size: float
    std_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int
    avg_sentence_completeness: float  # Porcentaje de oraciones completas
    avg_paragraph_preservation: float  # Porcentaje de párrafos preservados
    semantic_coherence_score: Optional[float] = None  # Score de coherencia semántica
    overlap_efficiency: Optional[float] = None  # Eficiencia del overlap


@dataclass
class ChunkingResult:
    """Resultado de una estrategia de chunking."""
    strategy: ChunkingStrategy
    chunks: List[Document]
    metrics: ChunkingMetrics
    config: Dict[str, Any]


class DocumentAnalyzer:
    """Analiza documentos para determinar sus características."""
    
    @staticmethod
    def detect_document_type(text: str, file_path: Optional[Path] = None) -> DocumentType:
        """
        Detecta el tipo de documento basándose en su contenido y extensión.
        
        Args:
            text: Contenido del documento
            file_path: Ruta del archivo (opcional)
            
        Returns:
            Tipo de documento detectado
        """
        # Detectar por extensión
        if file_path:
            ext = file_path.suffix.lower()
            if ext == '.md' or ext == '.markdown':
                return DocumentType.MARKDOWN
            elif ext == '.html' or ext == '.htm':
                return DocumentType.HTML
            elif ext == '.py':
                return DocumentType.PYTHON
        
        # Detectar por contenido
        # Markdown
        if re.search(r'^#{1,6}\s+', text, re.MULTILINE):
            return DocumentType.MARKDOWN
        
        # HTML
        if re.search(r'<[a-z][\s\S]*>', text):
            return DocumentType.HTML
        
        # Python code
        python_keywords = ['def ', 'class ', 'import ', 'from ', 'if __name__']
        if any(keyword in text for keyword in python_keywords):
            if re.search(r'def\s+\w+\s*\(|class\s+\w+|import\s+\w+', text):
                return DocumentType.PYTHON
        
        # Estructura técnica (listas numeradas, código, etc.)
        if re.search(r'^\d+\.\s+|```|`\w+`', text, re.MULTILINE):
            return DocumentType.TECHNICAL
        
        # Narrativo (muchas oraciones, párrafos largos)
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if avg_sentence_length > 15 and len(sentences) > 5:
            return DocumentType.NARRATIVE
        
        return DocumentType.UNSTRUCTURED
    
    @staticmethod
    def analyze_structure(text: str) -> Dict[str, Any]:
        """
        Analiza la estructura del documento.
        
        Returns:
            Diccionario con métricas de estructura
        """
        # Contar elementos estructurales
        headers = len(re.findall(r'^#{1,6}\s+', text, re.MULTILINE))
        paragraphs = len(re.split(r'\n\s*\n', text))
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        characters = len(text)
        
        # Detectar listas
        bullet_lists = len(re.findall(r'^[\*\-\+]\s+', text, re.MULTILINE))
        numbered_lists = len(re.findall(r'^\d+\.\s+', text, re.MULTILINE))
        
        # Calcular densidad de estructura
        structure_density = (headers + bullet_lists + numbered_lists) / max(paragraphs, 1)
        
        return {
            'headers': headers,
            'paragraphs': paragraphs,
            'sentences': sentences,
            'words': words,
            'characters': characters,
            'bullet_lists': bullet_lists,
            'numbered_lists': numbered_lists,
            'structure_density': structure_density,
            'avg_sentence_length': words / max(sentences, 1),
            'avg_paragraph_length': words / max(paragraphs, 1),
        }
    
    @staticmethod
    def calculate_optimal_chunk_size(
        text: str,
        model_max_tokens: Optional[int] = None,
        target_chunks: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Calcula el tamaño óptimo de chunk y overlap.
        
        Args:
            text: Texto a dividir
            model_max_tokens: Máximo de tokens del modelo (opcional)
            target_chunks: Número objetivo de chunks (opcional)
            
        Returns:
            Tupla (chunk_size, chunk_overlap)
        """
        text_length = len(text)
        
        # Si hay un modelo específico, usar sus límites
        if model_max_tokens:
            # Aproximación: 1 token ≈ 4 caracteres
            max_chars = model_max_tokens * 4
            # Usar 80% del máximo para dejar margen
            chunk_size = int(max_chars * 0.8)
        elif target_chunks:
            # Calcular basándose en número objetivo de chunks
            chunk_size = text_length // target_chunks
        else:
            # Valores por defecto basados en mejores prácticas
            if text_length < 5000:
                chunk_size = 1000
            elif text_length < 50000:
                chunk_size = 2000
            else:
                chunk_size = 3000
        
        # Overlap: 10-20% del chunk_size
        chunk_overlap = max(int(chunk_size * 0.15), 50)
        
        return chunk_size, chunk_overlap


class ChunkingEvaluator:
    """Evalúa la calidad de diferentes estrategias de chunking."""
    
    @staticmethod
    def calculate_metrics(
        chunks: List[Document],
        original_text: str
    ) -> ChunkingMetrics:
        """
        Calcula métricas de calidad para los chunks generados.
        
        Args:
            chunks: Lista de chunks generados
            original_text: Texto original completo
            
        Returns:
            Métricas calculadas
        """
        if not chunks:
            raise ValueError("No se pueden calcular métricas sin chunks")
        
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        num_chunks = len(chunks)
        avg_chunk_size = sum(chunk_sizes) / num_chunks
        std_chunk_size = (
            sum((x - avg_chunk_size) ** 2 for x in chunk_sizes) / num_chunks
        ) ** 0.5
        
        # Calcular completitud de oraciones
        sentence_completeness = []
        for chunk in chunks:
            text = chunk.page_content
            # Contar oraciones completas (terminan en . ! ?)
            complete_sentences = len(re.findall(r'[.!?]\s+', text))
            total_sentences = len(re.split(r'[.!?]+', text))
            if total_sentences > 0:
                completeness = complete_sentences / total_sentences
                sentence_completeness.append(completeness)
        
        avg_sentence_completeness = (
            sum(sentence_completeness) / len(sentence_completeness)
            if sentence_completeness else 0.0
        )
        
        # Calcular preservación de párrafos
        original_paragraphs = re.split(r'\n\s*\n', original_text)
        paragraph_preservation = []
        for chunk in chunks:
            chunk_text = chunk.page_content
            preserved = sum(1 for para in original_paragraphs if para.strip() in chunk_text)
            if original_paragraphs:
                preservation = preserved / len(original_paragraphs)
                paragraph_preservation.append(preservation)
        
        avg_paragraph_preservation = (
            sum(paragraph_preservation) / len(paragraph_preservation)
            if paragraph_preservation else 0.0
        )
        
        return ChunkingMetrics(
            num_chunks=num_chunks,
            avg_chunk_size=avg_chunk_size,
            std_chunk_size=std_chunk_size,
            min_chunk_size=min(chunk_sizes),
            max_chunk_size=max(chunk_sizes),
            avg_sentence_completeness=avg_sentence_completeness,
            avg_paragraph_preservation=avg_paragraph_preservation,
        )
    
    @staticmethod
    def score_strategy(metrics: ChunkingMetrics) -> float:
        """
        Calcula un score general para una estrategia de chunking.
        
        Score más alto = mejor estrategia
        
        Args:
            metrics: Métricas de la estrategia
            
        Returns:
            Score numérico (0-100)
        """
        # Factores de evaluación:
        # 1. Completitud de oraciones (peso: 30%)
        sentence_score = metrics.avg_sentence_completeness * 30
        
        # 2. Preservación de párrafos (peso: 25%)
        paragraph_score = metrics.avg_paragraph_preservation * 25
        
        # 3. Consistencia de tamaño (menor std = mejor) (peso: 20%)
        # Normalizar std (asumiendo que std < avg es bueno)
        consistency_score = max(0, 20 * (1 - metrics.std_chunk_size / max(metrics.avg_chunk_size, 1)))
        
        # 4. Número razonable de chunks (peso: 15%)
        # Idealmente entre 5-50 chunks para documentos medianos
        if 5 <= metrics.num_chunks <= 50:
            count_score = 15
        elif metrics.num_chunks < 5:
            count_score = 15 * (metrics.num_chunks / 5)
        else:
            # Penalizar demasiados chunks
            count_score = max(0, 15 * (50 / metrics.num_chunks))
        
        # 5. Tamaño mínimo razonable (peso: 10%)
        # Chunks muy pequeños son problemáticos
        if metrics.min_chunk_size >= 100:
            size_score = 10
        else:
            size_score = 10 * (metrics.min_chunk_size / 100)
        
        total_score = sentence_score + paragraph_score + consistency_score + count_score + size_score
        
        return min(100, max(0, total_score))


class ChunkingMaster:
    """Función maestra para seleccionar y aplicar la mejor estrategia de chunking."""
    
    def __init__(
        self,
        embedding_model=None,
        model_max_tokens: Optional[int] = None,
        preferred_strategy: Optional[ChunkingStrategy] = None
    ):
        """
        Inicializa el ChunkingMaster.
        
        Args:
            embedding_model: Modelo de embeddings para chunking semántico (opcional)
            model_max_tokens: Máximo de tokens del modelo LLM objetivo (opcional)
            preferred_strategy: Estrategia preferida (opcional, si None se selecciona automáticamente)
        """
        self.embedding_model = embedding_model
        self.model_max_tokens = model_max_tokens
        self.preferred_strategy = preferred_strategy
        self.analyzer = DocumentAnalyzer()
        self.evaluator = ChunkingEvaluator()
    
    def _create_splitter(
        self,
        strategy: ChunkingStrategy,
        chunk_size: int,
        chunk_overlap: int,
        **kwargs
    ):
        """Crea un splitter según la estrategia especificada."""
        if strategy == ChunkingStrategy.CHARACTER:
            return CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        elif strategy == ChunkingStrategy.RECURSIVE:
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        elif strategy == ChunkingStrategy.TOKEN:
            return TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        elif strategy == ChunkingStrategy.MARKDOWN_HEADER:
            headers_to_split_on = kwargs.get(
                'headers_to_split_on',
                [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3"),
                ]
            )
            # MarkdownHeaderTextSplitter necesita un segundo splitter para dividir los chunks
            md_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            # Crear un splitter recursivo para dividir después de agrupar por headers
            recursive_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            # Retornar ambos splitters como tupla para procesamiento especial
            return (md_splitter, recursive_splitter)
        
        elif strategy == ChunkingStrategy.HTML_HEADER:
            return HTMLHeaderTextSplitter()
        
        elif strategy == ChunkingStrategy.PYTHON_CODE:
            return PythonCodeTextSplitter()
        
        elif strategy == ChunkingStrategy.SEMANTIC:
            if SemanticChunker is None:
                raise ValueError(
                    "SemanticChunker no está disponible. Instale langchain-experimental."
                )
            if not self.embedding_model:
                raise ValueError(
                    "Se requiere un modelo de embeddings para chunking semántico"
                )
            return SemanticChunker(
                embeddings=self.embedding_model,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=kwargs.get('breakpoint_threshold', 95)
            )
        
        elif strategy == ChunkingStrategy.LANGUAGE_SPECIFIC:
            if LanguageParser is None:
                raise ValueError(
                    "LanguageParser no está disponible. Use PythonCodeTextSplitter en su lugar."
                )
            language = kwargs.get('language', Language.PYTHON)
            return LanguageParser(language=language)
        
        else:
            raise ValueError(f"Estrategia no soportada: {strategy}")
    
    def _select_candidate_strategies(
        self,
        doc_type: DocumentType,
        structure: Dict[str, Any]
    ) -> List[ChunkingStrategy]:
        """
        Selecciona estrategias candidatas basándose en el tipo y estructura del documento.
        
        Returns:
            Lista de estrategias candidatas ordenadas por relevancia
        """
        candidates = []
        
        # Estrategias específicas por tipo de documento
        if doc_type == DocumentType.MARKDOWN:
            if structure['headers'] > 0:
                candidates.append(ChunkingStrategy.MARKDOWN_HEADER)
            candidates.append(ChunkingStrategy.RECURSIVE)
        
        elif doc_type == DocumentType.HTML:
            candidates.append(ChunkingStrategy.HTML_HEADER)
            candidates.append(ChunkingStrategy.RECURSIVE)
        
        elif doc_type == DocumentType.PYTHON:
            candidates.append(ChunkingStrategy.PYTHON_CODE)
            candidates.append(ChunkingStrategy.LANGUAGE_SPECIFIC)
            candidates.append(ChunkingStrategy.RECURSIVE)
        
        # Estrategias basadas en estructura
        if structure['structure_density'] > 0.5:
            # Documento bien estructurado
            candidates.append(ChunkingStrategy.RECURSIVE)
        else:
            # Documento menos estructurado
            candidates.append(ChunkingStrategy.RECURSIVE)
            candidates.append(ChunkingStrategy.CHARACTER)
        
        # Chunking semántico para documentos narrativos o largos
        if doc_type == DocumentType.NARRATIVE or structure['words'] > 10000:
            if self.embedding_model and SemanticChunker is not None:
                candidates.append(ChunkingStrategy.SEMANTIC)
        
        # Token-based para modelos específicos
        if self.model_max_tokens:
            candidates.append(ChunkingStrategy.TOKEN)
        
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        
        # Si no hay candidatos, usar recursivo como fallback
        if not unique_candidates:
            unique_candidates.append(ChunkingStrategy.RECURSIVE)
        
        return unique_candidates
    
    def find_best_chunking_strategy(
        self,
        documents: List[Document],
        file_path: Optional[Path] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        evaluate_all: bool = False
    ) -> ChunkingResult:
        """
        Encuentra y aplica la mejor estrategia de chunking para los documentos dados.
        
        Args:
            documents: Lista de documentos LangChain a dividir
            file_path: Ruta del archivo original (opcional, ayuda a detectar tipo)
            chunk_size: Tamaño de chunk deseado (opcional, se calcula automáticamente)
            chunk_overlap: Overlap deseado (opcional, se calcula automáticamente)
            evaluate_all: Si True, evalúa todas las estrategias candidatas y selecciona la mejor
            
        Returns:
            ChunkingResult con la mejor estrategia y sus chunks
        """
        if not documents:
            raise ValueError("Se requiere al menos un documento")
        
        # Combinar todos los documentos en un solo texto para análisis
        full_text = "\n\n".join([doc.page_content for doc in documents])
        
        # Analizar documento
        doc_type = self.analyzer.detect_document_type(full_text, file_path)
        structure = self.analyzer.analyze_structure(full_text)
        
        logger.info(f"Tipo de documento detectado: {doc_type.value}")
        logger.info(f"Estructura: {structure['headers']} headers, "
                   f"{structure['paragraphs']} párrafos, "
                   f"{structure['words']} palabras")
        
        # Calcular parámetros óptimos si no se proporcionan
        if chunk_size is None or chunk_overlap is None:
            chunk_size, chunk_overlap = self.analyzer.calculate_optimal_chunk_size(
                full_text,
                self.model_max_tokens
            )
            logger.info(f"Parámetros calculados: chunk_size={chunk_size}, "
                       f"chunk_overlap={chunk_overlap}")
        
        # Si hay estrategia preferida y no se requiere evaluación completa
        if self.preferred_strategy and not evaluate_all:
            logger.info(f"Usando estrategia preferida: {self.preferred_strategy.value}")
            return self._apply_strategy(
                self.preferred_strategy,
                documents,
                chunk_size,
                chunk_overlap,
                doc_type,
                structure
            )
        
        # Seleccionar estrategias candidatas
        candidate_strategies = self._select_candidate_strategies(doc_type, structure)
        logger.info(f"Estrategias candidatas: {[s.value for s in candidate_strategies]}")
        
        # Evaluar estrategias
        results = []
        for strategy in candidate_strategies:
            try:
                result = self._apply_strategy(
                    strategy,
                    documents,
                    chunk_size,
                    chunk_overlap,
                    doc_type,
                    structure
                )
                results.append(result)
                logger.info(f"Estrategia {strategy.value}: "
                           f"{result.metrics.num_chunks} chunks, "
                           f"score={self.evaluator.score_strategy(result.metrics):.2f}")
            except Exception as e:
                logger.warning(f"Error al aplicar estrategia {strategy.value}: {e}")
                continue
        
        if not results:
            raise RuntimeError("No se pudo aplicar ninguna estrategia de chunking")
        
        # Seleccionar la mejor estrategia basándose en el score
        best_result = max(results, key=lambda r: self.evaluator.score_strategy(r.metrics))
        
        logger.info(f"Mejor estrategia seleccionada: {best_result.strategy.value} "
                   f"(score: {self.evaluator.score_strategy(best_result.metrics):.2f})")
        
        return best_result
    
    def _apply_strategy(
        self,
        strategy: ChunkingStrategy,
        documents: List[Document],
        chunk_size: int,
        chunk_overlap: int,
        doc_type: DocumentType,
        structure: Dict[str, Any]
    ) -> ChunkingResult:
        """Aplica una estrategia específica de chunking."""
        # Crear splitter
        # Preparar kwargs para el splitter
        splitter_kwargs = {}
        if strategy == ChunkingStrategy.LANGUAGE_SPECIFIC and doc_type == DocumentType.PYTHON:
            if Language is not None:
                splitter_kwargs['language'] = Language.PYTHON
        
        splitter = self._create_splitter(
            strategy,
            chunk_size,
            chunk_overlap,
            **splitter_kwargs
        )
        
        # Aplicar splitter
        if strategy == ChunkingStrategy.MARKDOWN_HEADER:
            # MarkdownHeaderTextSplitter requiere procesamiento en dos pasos
            md_splitter, recursive_splitter = splitter
            # Primero agrupar por headers
            header_groups = md_splitter.split_text(documents[0].page_content)
            # Luego dividir cada grupo con el splitter recursivo
            chunks = []
            for group in header_groups:
                group_doc = Document(page_content=group.page_content, metadata=group.metadata)
                group_chunks = recursive_splitter.split_documents([group_doc])
                chunks.extend(group_chunks)
        elif strategy == ChunkingStrategy.HTML_HEADER:
            # HTMLHeaderTextSplitter también puede necesitar procesamiento especial
            try:
                chunks = splitter.split_documents(documents)
            except AttributeError:
                # Si no tiene split_documents, usar split_text
                chunks = []
                for doc in documents:
                    text_chunks = splitter.split_text(doc.page_content)
                    for chunk_text in text_chunks:
                        chunks.append(Document(page_content=chunk_text, metadata=doc.metadata.copy()))
        else:
            chunks = splitter.split_documents(documents)
        
        # Calcular métricas
        full_text = "\n\n".join([doc.page_content for doc in documents])
        metrics = self.evaluator.calculate_metrics(chunks, full_text)
        
        # Crear resultado
        config = {
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'doc_type': doc_type.value,
            'structure': structure
        }
        
        return ChunkingResult(
            strategy=strategy,
            chunks=chunks,
            metrics=metrics,
            config=config
        )


def master_chunking_function(
    documents: List[Document],
    file_path: Optional[Path] = None,
    embedding_model=None,
    model_max_tokens: Optional[int] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    preferred_strategy: Optional[str] = None,
    evaluate_all: bool = False
) -> Tuple[List[Document], Dict[str, Any]]:
    """
    Función maestra para chunking inteligente.
    
    Esta función analiza los documentos, evalúa diferentes estrategias de chunking
    y selecciona la mejor basándose en métricas de calidad.
    
    Args:
        documents: Lista de documentos LangChain a dividir
        file_path: Ruta del archivo original (opcional)
        embedding_model: Modelo de embeddings para chunking semántico (opcional)
        model_max_tokens: Máximo de tokens del modelo LLM objetivo (opcional)
        chunk_size: Tamaño de chunk deseado (opcional, se calcula automáticamente)
        chunk_overlap: Overlap deseado (opcional, se calcula automáticamente)
        preferred_strategy: Estrategia preferida como string (opcional)
        evaluate_all: Si True, evalúa todas las estrategias candidatas
    
    Returns:
        Tupla (chunks, metadata) donde:
        - chunks: Lista de documentos divididos
        - metadata: Diccionario con información sobre la estrategia seleccionada
    
    Ejemplo:
        >>> from langchain_core.documents import Document
        >>> docs = [Document(page_content="Tu texto aquí...")]
        >>> chunks, metadata = master_chunking_function(docs)
        >>> print(f"Estrategia: {metadata['strategy']}")
        >>> print(f"Número de chunks: {metadata['num_chunks']}")
    """
    # Convertir preferred_strategy a enum si se proporciona
    strategy_enum = None
    if preferred_strategy:
        try:
            strategy_enum = ChunkingStrategy(preferred_strategy.lower())
        except ValueError:
            logger.warning(f"Estrategia '{preferred_strategy}' no reconocida, "
                          "se seleccionará automáticamente")
    
    # Crear ChunkingMaster
    master = ChunkingMaster(
        embedding_model=embedding_model,
        model_max_tokens=model_max_tokens,
        preferred_strategy=strategy_enum
    )
    
    # Encontrar mejor estrategia
    result = master.find_best_chunking_strategy(
        documents=documents,
        file_path=file_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        evaluate_all=evaluate_all
    )
    
    # Preparar metadata
    metadata = {
        'strategy': result.strategy.value,
        'num_chunks': result.metrics.num_chunks,
        'avg_chunk_size': result.metrics.avg_chunk_size,
        'min_chunk_size': result.metrics.min_chunk_size,
        'max_chunk_size': result.metrics.max_chunk_size,
        'sentence_completeness': result.metrics.avg_sentence_completeness,
        'paragraph_preservation': result.metrics.avg_paragraph_preservation,
        'quality_score': master.evaluator.score_strategy(result.metrics),
        'config': result.config
    }
    
    return result.chunks, metadata

