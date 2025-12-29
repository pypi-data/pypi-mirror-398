"""
Interfaz de Servicio: InferenceService

Define las operaciones para extraer entidades, relaciones y facts desde chunks.

Nota sobre implementaciones alternativas:
La extracción de entidades y relaciones puede realizarse también usando LLMs
(OpenAI, Claude, Gemini, Llama3, etc.) para obtener mayor flexibilidad y
capacidad de extraer relaciones complejas. Para referencia, ver el trabajo
de Neo4j con LLM Graph Builder:
https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/

El LLM Graph Builder de Neo4j usa modelos LLM para transformar texto no
estructurado en grafos de conocimiento, extrayendo entidades y relaciones
con mayor precisión que NER tradicional. Utiliza el módulo llm-graph-transformer
que Neo4j contribuyó a LangChain.

La implementación actual (v0.1.0) usa spaCy (NER-only) como solución mínima
viable. Implementaciones LLM pueden añadirse en futuras versiones siguiendo
el mismo patrón de arquitectura Clean Architecture.
"""

from abc import ABC, abstractmethod
from typing import List
from domain.entities.chunk import Chunk
from domain.entities.fact import Fact
from domain.entities.entity import Entity
from domain.entities.relation import Relation


class InferenceService(ABC):
    """
    Interfaz que define las operaciones para inferencia de conocimiento.
    
    Un servicio de inferencia extrae entidades, relaciones y facts estructurados
    desde chunks de texto. Las implementaciones pueden usar diferentes técnicas:
    - NER (Named Entity Recognition) con spaCy, transformers, etc.
    - LLMs (OpenAI, Claude, Gemini) para extracción más flexible
    - Híbridas (NER + LLM) para mejor precisión
    
    La implementación de referencia para v0.1.0 es SpacyInferenceService,
    que usa spaCy para NER básico. Implementaciones LLM pueden añadirse
    siguiendo el mismo patrón.
    
    Referencias:
    - Neo4j LLM Graph Builder: https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/
    - LangChain KG Construction: https://python.langchain.com/v0.1/docs/use_cases/graph/constructing/
    """
    
    @abstractmethod
    def extract_entities(self, chunk: Chunk) -> List[Entity]:
        """
        Extrae entidades nombradas del chunk.
        
        Las entidades pueden ser personas, organizaciones, lugares, conceptos, etc.
        El tipo y precisión dependen de la implementación:
        - NER tradicional: tipos estándar (PERSON, ORG, LOC, etc.)
        - LLM: tipos más flexibles y específicos del dominio
        
        Args:
            chunk: Chunk de texto del cual extraer entidades
        
        Returns:
            Lista de entidades Entity extraídas
        
        Raises:
            ValueError: Si el chunk es inválido
        """
        pass
    
    @abstractmethod
    def extract_relations(self, chunk: Chunk, entities: List[Entity]) -> List[Relation]:
        """
        Extrae relaciones entre entidades del chunk.
        
        Las relaciones conectan entidades identificadas en el chunk.
        El tipo y complejidad dependen de la implementación:
        - NER básico: relaciones simples (MENTIONS, CO_OCCURS_WITH)
        - LLM: relaciones semánticas complejas (WORKS_FOR, LOCATED_IN, etc.)
        
        Args:
            chunk: Chunk de texto del cual extraer relaciones
            entities: Lista de entidades previamente extraídas del chunk
        
        Returns:
            Lista de relaciones Relation extraídas
        
        Raises:
            ValueError: Si el chunk o las entidades son inválidos
        """
        pass
    
    @abstractmethod
    def infer_facts(self, chunk: Chunk) -> List[Fact]:
        """
        Genera facts estructurados (subject-predicate-object) desde el chunk.
        
        Un fact es una tripleta que representa conocimiento derivado del chunk.
        Incluye información de confianza y trazabilidad (provenance).
        
        La implementación puede usar diferentes estrategias:
        - NER: facts simples (chunk_id, "MENTIONS", entity_name)
        - LLM: facts complejos con relaciones semánticas
        
        Args:
            chunk: Chunk de texto del cual inferir facts
        
        Returns:
            Lista de facts Fact con subject, predicate, object, confidence y provenance
        
        Raises:
            ValueError: Si el chunk es inválido
        """
        pass




