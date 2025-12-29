"""
LLM-based Inference Service

Implements InferenceService interface using LangChain's LLMGraphTransformer
for entity and relationship extraction from text chunks.

This implementation uses a Language Model (LLM) to extract structured knowledge
from unstructured text, producing entities, relationships, and facts suitable
for knowledge graph construction.

Architecture:
    - LLMInferenceService: Main service implementing InferenceService interface
    - LangChainAdapter: Helper class for type conversion between LangChain
      and Ungraph domain entities

Dependencies:
    - langchain_experimental.graph_transformers.LLMGraphTransformer
    - langchain_core.documents.Document
    - langchain_community.graphs.graph_document.GraphDocument

Usage:
    from langchain_openai import ChatOpenAI
    from src.infrastructure.services.llm_inference_service import LLMInferenceService
    
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    service = LLMInferenceService(
        llm=llm,
        allowed_nodes=["Person", "Organization", "Location"],
        allowed_relationships=["WORKS_FOR", "LOCATED_IN"]
    )
    
    entities = service.extract_entities(chunk)
    relations = service.extract_relations(chunk, entities)
    facts = service.infer_facts(chunk)

Status: Experimental (v0.1.0)

Note: This implementation provides basic LLM-based extraction. Advanced features
like dynamic example selection, confidence scoring, and Opik evaluation are
planned for v0.2.0.
"""

from typing import List, Optional, Any
from uuid import uuid4

from langchain_core.documents import Document as LangChainDocument
from langchain_core.language_models import BaseLanguageModel
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import (
    GraphDocument,
    Node as LangChainNode,
    Relationship as LangChainRelationship,
)

from domain.entities.chunk import Chunk
from domain.entities.entity import Entity
from domain.entities.fact import Fact
from domain.entities.relation import Relation
from domain.services.inference_service import InferenceService


class LangChainAdapter:
    """
    Adapter for converting between LangChain and Ungraph domain entities.
    
    This adapter handles bidirectional conversion:
    - Ungraph Chunk → LangChain Document
    - LangChain GraphDocument → Ungraph Entity/Relation/Fact
    
    The adapter ensures type safety and data integrity during conversion,
    handling edge cases like missing properties or invalid references.
    
    Design Pattern: Adapter Pattern (structural)
    Responsibility: Type conversion only, no business logic
    """
    
    @staticmethod
    def chunk_to_langchain_document(chunk: Chunk) -> LangChainDocument:
        """
        Convert Ungraph Chunk to LangChain Document.
        
        Args:
            chunk: Source chunk entity from domain layer
            
        Returns:
            LangChain Document with content and metadata
            
        Example:
            >>> chunk = Chunk(
            ...     id="chunk_1",
            ...     page_content="Apple Inc. is located in Cupertino.",
            ...     metadata={"filename": "doc.txt"}
            ... )
            >>> doc = LangChainAdapter.chunk_to_langchain_document(chunk)
            >>> doc.page_content
            'Apple Inc. is located in Cupertino.'
        """
        return LangChainDocument(
            page_content=chunk.page_content,
            metadata={
                **chunk.metadata,
                "chunk_id": chunk.id,
                "chunk_id_consecutive": chunk.chunk_id_consecutive,
            },
        )
    
    @staticmethod
    def langchain_nodes_to_entities(
        nodes: List[LangChainNode],
        chunk_id: str,
    ) -> List[Entity]:
        """
        Convert LangChain Nodes to Ungraph Entities.
        
        Args:
            nodes: List of LangChain Node objects
            chunk_id: Source chunk ID for provenance tracking
            
        Returns:
            List of Ungraph Entity objects
            
        Note:
            Each Node becomes an Entity with:
            - name: From node.id (human-readable identifier)
            - type: From node.type (entity category), or "UNKNOWN" if empty/None
            - mentions: Single-element list with source chunk_id
        """
        entities = []
        for node in nodes:
            # Handle empty or None type
            entity_type = node.type if node.type and node.type.strip() else "UNKNOWN"
            entity = Entity(
                id=f"entity_{uuid4().hex[:8]}",
                name=node.id,
                type=entity_type,
                mentions=[chunk_id],
            )
            entities.append(entity)
        return entities
    
    @staticmethod
    def langchain_relationships_to_relations(
        relationships: List[LangChainRelationship],
        entities: List[Entity],
        chunk_id: str,
    ) -> List[Relation]:
        """
        Convert LangChain Relationships to Ungraph Relations.
        
        Args:
            relationships: List of LangChain Relationship objects
            entities: Corresponding entities for ID resolution
            chunk_id: Source chunk ID for provenance tracking
            
        Returns:
            List of Ungraph Relation objects
            
        Note:
            Entity resolution: Maps node.id (name) to Entity.id via lookup.
            If source or target entity not found, relation is skipped.
            Default confidence: 0.8 (reasonable baseline for LLM extraction)
        """
        # Create lookup: entity_name → entity_id
        entity_lookup = {entity.name: entity.id for entity in entities}
        
        relations = []
        for rel in relationships:
            source_id = entity_lookup.get(rel.source.id)
            target_id = entity_lookup.get(rel.target.id)
            
            # Skip if entities not found (data integrity)
            if not source_id or not target_id:
                continue
            
            relation = Relation(
                id=f"relation_{uuid4().hex[:8]}",
                source_entity_id=source_id,
                target_entity_id=target_id,
                relation_type=rel.type,
                confidence=0.8,  # Default confidence for LLM extraction
                provenance_ref=chunk_id,
            )
            relations.append(relation)
        return relations
    
    @staticmethod
    def entities_to_facts(entities: List[Entity], chunk_id: str) -> List[Fact]:
        """
        Convert entities to MENTIONS facts for knowledge graph.
        
        Args:
            entities: List of extracted entities
            chunk_id: Source chunk ID
            
        Returns:
            List of Fact objects representing chunk-entity relationships
            
        Note:
            Each entity generates one MENTIONS fact:
            - subject: chunk_id
            - predicate: "MENTIONS"
            - object: entity.name
            - confidence: 1.0 (entity extraction confirmed)
        """
        facts = []
        for entity in entities:
            fact = Fact(
                id=f"fact_{uuid4().hex[:8]}",
                subject=chunk_id,
                predicate="MENTIONS",
                object=entity.name,
                confidence=1.0,
                provenance_ref=chunk_id,
            )
            facts.append(fact)
        return facts


class LLMInferenceService(InferenceService):
    """
    LLM-based implementation of InferenceService.
    
    Uses LangChain's LLMGraphTransformer to extract entities, relationships,
    and facts from text chunks using a Language Model (LLM).
    
    This implementation delegates to LLMGraphTransformer for extraction logic,
    focusing on integration with Ungraph's domain model via LangChainAdapter.
    
    Attributes:
        transformer: LLMGraphTransformer instance for extraction
        adapter: LangChainAdapter for type conversion
        
    Configuration:
        - allowed_nodes: List of permitted entity types (e.g., ["Person", "Company"])
        - allowed_relationships: List of permitted relation types (e.g., ["WORKS_FOR"])
        - prompt: Optional custom ChatPromptTemplate (defaults to LLMGraphTransformer's)
        - strict_mode: Enable filtering to allowed_nodes/allowed_relationships (default: True)
        
    Performance Characteristics:
        - Latency: ~2-5s per chunk (LLM-dependent)
        - Accuracy: Higher than NER for complex domains (domain-dependent)
        - Cost: LLM API calls required
        
    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = ChatOpenAI(model="gpt-4", temperature=0)
        >>> service = LLMInferenceService(
        ...     llm=llm,
        ...     allowed_nodes=["Person", "Organization"],
        ...     allowed_relationships=["WORKS_FOR"]
        ... )
        >>> chunk = Chunk(id="1", page_content="Alice works at Google.", metadata={})
        >>> entities = service.extract_entities(chunk)
        >>> len(entities)
        2
    """
    
    def __init__(
        self,
        llm: BaseLanguageModel,
        allowed_nodes: Optional[List[str]] = None,
        allowed_relationships: Optional[List[str]] = None,
        prompt: Optional[Any] = None,
        strict_mode: bool = True,
    ) -> None:
        """
        Initialize LLMInferenceService with LLM and schema configuration.
        
        Args:
            llm: LangChain-compatible language model (e.g., ChatOpenAI, ChatOllama)
            allowed_nodes: Permitted entity types. If None, all types allowed.
            allowed_relationships: Permitted relation types. If None, all types allowed.
            prompt: Custom ChatPromptTemplate for extraction. If None, uses default.
            strict_mode: If True, filter results to allowed_nodes/allowed_relationships.
                        If False, permit all extracted types (useful for exploration).
                        
        Raises:
            ValueError: If llm is None or not a BaseLanguageModel
            
        Note:
            Default allowed_nodes and allowed_relationships are empty lists,
            which means LLMGraphTransformer will extract all types found.
            Set strict_mode=True to enforce filtering.
        """
        if llm is None:
            raise ValueError("llm parameter is required and cannot be None")
        
        # Use empty lists as defaults (allow all types)
        self.allowed_nodes = allowed_nodes or []
        self.allowed_relationships = allowed_relationships or []
        
        # Initialize LangChain transformer
        self.transformer = LLMGraphTransformer(
            llm=llm,
            allowed_nodes=self.allowed_nodes,
            allowed_relationships=self.allowed_relationships,
            prompt=prompt,
            strict_mode=strict_mode,
        )
        
        # Initialize adapter
        self.adapter = LangChainAdapter()
    
    def extract_entities(self, chunk: Chunk) -> List[Entity]:
        """
        Extract entities from chunk using LLM.
        
        Args:
            chunk: Input chunk containing text to analyze
            
        Returns:
            List of Entity objects extracted from chunk
            
        Process:
            1. Convert Chunk to LangChain Document
            2. Process with LLMGraphTransformer
            3. Extract nodes from GraphDocument
            4. Convert nodes to Entity objects
            
        Example:
            >>> chunk = Chunk(
            ...     id="chunk_1",
            ...     page_content="Apple Inc. released iPhone 15.",
            ...     metadata={}
            ... )
            >>> entities = service.extract_entities(chunk)
            >>> [e.name for e in entities]
            ['Apple Inc.', 'iPhone 15']
        """
        # Convert to LangChain format
        document = self.adapter.chunk_to_langchain_document(chunk)
        
        # Process with LLMGraphTransformer
        graph_document = self.transformer.process_response(document)
        
        # Convert nodes to entities
        entities = self.adapter.langchain_nodes_to_entities(
            nodes=graph_document.nodes,
            chunk_id=chunk.id,
        )
        
        return entities
    
    def extract_relations(
        self,
        chunk: Chunk,
        entities: List[Entity],
    ) -> List[Relation]:
        """
        Extract relations between entities from chunk using LLM.
        
        Args:
            chunk: Input chunk containing text to analyze
            entities: Previously extracted entities from same chunk
            
        Returns:
            List of Relation objects connecting entities
            
        Note:
            This method re-processes the chunk to extract relationships.
            The entities parameter is used for ID resolution during conversion.
            
        Process:
            1. Convert Chunk to LangChain Document
            2. Process with LLMGraphTransformer
            3. Extract relationships from GraphDocument
            4. Convert relationships to Relation objects using entity lookup
            
        Example:
            >>> relations = service.extract_relations(chunk, entities)
            >>> rel = relations[0]
            >>> rel.relation_type
            'PRODUCED_BY'
        """
        # Convert to LangChain format
        document = self.adapter.chunk_to_langchain_document(chunk)
        
        # Process with LLMGraphTransformer
        graph_document = self.transformer.process_response(document)
        
        # Convert relationships to relations
        relations = self.adapter.langchain_relationships_to_relations(
            relationships=graph_document.relationships,
            entities=entities,
            chunk_id=chunk.id,
        )
        
        return relations
    
    def infer_facts(self, chunk: Chunk) -> List[Fact]:
        """
        Infer facts from chunk (entity mentions).
        
        Args:
            chunk: Input chunk containing text to analyze
            
        Returns:
            List of Fact objects representing chunk-entity relationships
            
        Note:
            This implementation generates MENTIONS facts from extracted entities.
            Each fact represents: chunk MENTIONS entity_name
            
        Process:
            1. Extract entities from chunk
            2. Generate MENTIONS fact for each entity
            
        Example:
            >>> facts = service.infer_facts(chunk)
            >>> fact = facts[0]
            >>> fact.predicate
            'MENTIONS'
        """
        # Extract entities
        entities = self.extract_entities(chunk)
        
        # Convert to MENTIONS facts
        facts = self.adapter.entities_to_facts(
            entities=entities,
            chunk_id=chunk.id,
        )
        
        return facts
