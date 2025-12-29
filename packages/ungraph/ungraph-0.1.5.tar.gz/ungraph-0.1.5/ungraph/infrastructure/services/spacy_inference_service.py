"""
Implementación: SpacyInferenceService

Implementa InferenceService usando spaCy para Named Entity Recognition (NER).

Esta es la implementación de referencia para el release v0.1.0.
Usa spaCy para extracción de entidades nombradas (NER) y genera
facts simples del tipo (chunk_id, "MENTIONS", entity_name).

Nota: Para extracción más avanzada con LLMs, ver documentación
de InferenceService y referencia a Neo4j LLM Graph Builder:
https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/
"""

import logging
import uuid
from typing import List, Dict, Set
from datetime import datetime

from ungraph.domain.services.inference_service import InferenceService
from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.fact import Fact
from ungraph.domain.entities.entity import Entity
from ungraph.domain.entities.relation import Relation

logger = logging.getLogger(__name__)

# Importar spaCy con manejo de errores
try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning(
        "spaCy no está instalado. Instala con: pip install spacy && python -m spacy download en_core_web_sm"
    )


class SpacyInferenceService(InferenceService):
    """
    Implementación de InferenceService usando spaCy para NER.
    
    Esta implementación:
    - Usa spaCy para extraer entidades nombradas (PERSON, ORG, LOC, etc.)
    - Genera facts simples: (chunk_id, "MENTIONS", entity_name)
    - Genera relaciones básicas entre entidades co-ocurrentes
    - Calcula confianza basada en el tipo de entidad y frecuencia
    
    Modelo por defecto: en_core_web_sm (inglés)
    Puede cambiarse pasando otro modelo en el constructor.
    
    Ejemplo:
        service = SpacyInferenceService(model_name="en_core_web_sm")
        facts = service.infer_facts(chunk)
    """
    
    # Mapeo de tipos de entidades de spaCy a tipos estándar
    ENTITY_TYPE_MAPPING: Dict[str, str] = {
        "PERSON": "PERSON",
        "ORG": "ORGANIZATION",
        "ORGANIZATION": "ORGANIZATION",
        "GPE": "LOCATION",  # Geopolitical entity
        "LOC": "LOCATION",
        "LOCATION": "LOCATION",
        "DATE": "DATE",
        "TIME": "TIME",
        "MONEY": "MONEY",
        "PERCENT": "PERCENT",
        "QUANTITY": "QUANTITY",
    }
    
    def __init__(self, model_name: str = "en_core_web_sm", disable: List[str] = None):
        """
        Inicializa el servicio de inferencia con spaCy.
        
        Args:
            model_name: Nombre del modelo de spaCy (default: en_core_web_sm)
            disable: Lista de componentes de spaCy a deshabilitar (para velocidad)
        
        Raises:
            ImportError: Si spaCy no está instalado
            OSError: Si el modelo no está disponible
        """
        if not SPACY_AVAILABLE:
            raise ImportError(
                "spaCy no está instalado. Instala con: "
                "pip install spacy && python -m spacy download en_core_web_sm"
            )
        
        self.model_name = model_name
        self.disable = disable or []
        
        try:
            logger.info(f"Loading spaCy model: {model_name}")
            self.nlp = spacy.load(model_name, disable=self.disable)
            logger.info(f"spaCy model loaded successfully")
        except OSError as e:
            logger.error(f"Error loading spaCy model {model_name}: {e}")
            raise OSError(
                f"Modelo spaCy '{model_name}' no encontrado. "
                f"Instala con: python -m spacy download {model_name}"
            ) from e
    
    def extract_entities(self, chunk: Chunk) -> List[Entity]:
        """
        Extrae entidades nombradas del chunk usando spaCy NER.
        
        Args:
            chunk: Chunk de texto del cual extraer entidades
        
        Returns:
            Lista de entidades Entity extraídas
        
        Raises:
            ValueError: Si el chunk es inválido
        """
        if not chunk or not chunk.page_content:
            raise ValueError("Chunk cannot be empty")
        
        logger.debug(f"Extracting entities from chunk: {chunk.id}")
        
        # Procesar texto con spaCy
        doc = self.nlp(chunk.page_content)
        
        # Extraer entidades únicas (por nombre y tipo)
        entities_dict: Dict[tuple[str, str], Entity] = {}
        
        for ent in doc.ents:
            # Normalizar tipo de entidad
            entity_type = self.ENTITY_TYPE_MAPPING.get(ent.label_, ent.label_)
            
            # Crear clave única (nombre, tipo)
            key = (ent.text.strip(), entity_type)
            
            if key not in entities_dict:
                # Crear nueva entidad
                entity_id = f"entity_{uuid.uuid4().hex[:8]}"
                entity = Entity(
                    id=entity_id,
                    name=ent.text.strip(),
                    type=entity_type,
                    mentions=[chunk.id]
                )
                entities_dict[key] = entity
            else:
                # Añadir mención si no existe
                entities_dict[key].add_mention(chunk.id)
        
        entities = list(entities_dict.values())
        logger.debug(f"Extracted {len(entities)} entities from chunk {chunk.id}")
        
        return entities
    
    def extract_relations(self, chunk: Chunk, entities: List[Entity]) -> List[Relation]:
        """
        Extrae relaciones básicas entre entidades co-ocurrentes.
        
        Para spaCy básico, generamos relaciones simples de co-ocurrencia.
        Implementaciones LLM pueden extraer relaciones semánticas más complejas.
        
        Args:
            chunk: Chunk de texto
            entities: Lista de entidades previamente extraídas
        
        Returns:
            Lista de relaciones Relation extraídas
        """
        if not entities:
            return []
        
        logger.debug(f"Extracting relations from {len(entities)} entities in chunk {chunk.id}")
        
        relations = []
        
        # Generar relaciones de co-ocurrencia entre entidades en el mismo chunk
        # Solo para entidades diferentes
        for i, source_entity in enumerate(entities):
            for target_entity in entities[i+1:]:
                # Crear relación de co-ocurrencia
                relation_id = f"rel_{uuid.uuid4().hex[:8]}"
                relation = Relation(
                    id=relation_id,
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relation_type="CO_OCCURS_WITH",
                    confidence=0.7,  # Confianza media para co-ocurrencia
                    provenance_ref=chunk.id
                )
                relations.append(relation)
        
        logger.debug(f"Extracted {len(relations)} relations from chunk {chunk.id}")
        
        return relations
    
    def infer_facts(self, chunk: Chunk) -> List[Fact]:
        """
        Genera facts estructurados desde el chunk usando spaCy NER.
        
        Genera facts del tipo: (chunk_id, "MENTIONS", entity_name)
        con confianza basada en el tipo de entidad.
        
        Args:
            chunk: Chunk de texto del cual inferir facts
        
        Returns:
            Lista de facts Fact con subject, predicate, object, confidence y provenance
        
        Raises:
            ValueError: Si el chunk es inválido
        """
        if not chunk or not chunk.page_content:
            raise ValueError("Chunk cannot be empty")
        
        logger.debug(f"Inferring facts from chunk: {chunk.id}")
        
        # Extraer entidades
        entities = self.extract_entities(chunk)
        
        # Generar facts: uno por cada entidad encontrada
        facts = []
        
        for entity in entities:
            # Calcular confianza basada en tipo de entidad
            # Entidades comunes (PERSON, ORG) tienen mayor confianza
            confidence_map = {
                "PERSON": 0.9,
                "ORGANIZATION": 0.9,
                "LOCATION": 0.85,
                "DATE": 0.8,
                "TIME": 0.75,
                "MONEY": 0.8,
                "PERCENT": 0.75,
            }
            confidence = confidence_map.get(entity.type, 0.7)
            
            # Crear fact: (chunk_id, "MENTIONS", entity_name)
            fact_id = f"fact_{uuid.uuid4().hex[:8]}"
            fact = Fact(
                id=fact_id,
                subject=chunk.id,
                predicate="MENTIONS",
                object=entity.name,
                confidence=confidence,
                provenance_ref=chunk.id
            )
            facts.append(fact)
        
        logger.info(f"Inferred {len(facts)} facts from chunk {chunk.id}")
        
        return facts
    
    def _calculate_entity_confidence(self, entity_type: str, frequency: int = 1) -> float:
        """
        Calcula confianza para una entidad basada en tipo y frecuencia.
        
        Args:
            entity_type: Tipo de entidad
            frequency: Frecuencia de aparición en el documento
        
        Returns:
            Valor de confianza entre 0.0 y 1.0
        """
        base_confidence = {
            "PERSON": 0.9,
            "ORGANIZATION": 0.9,
            "LOCATION": 0.85,
            "DATE": 0.8,
            "TIME": 0.75,
            "MONEY": 0.8,
            "PERCENT": 0.75,
        }.get(entity_type, 0.7)
        
        # Aumentar confianza si aparece múltiples veces
        frequency_boost = min(0.1 * (frequency - 1), 0.1)
        
        return min(base_confidence + frequency_boost, 1.0)




