"""
Implementación concreta: Neo4jChunkRepository

Implementa ChunkRepository usando Neo4j.
Envuelve el código existente de graph_operations.py.
"""

from typing import List, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError
import logging

from ungraph.domain.repositories.chunk_repository import ChunkRepository
from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.fact import Fact
from ungraph.domain.entities.entity import Entity
from ungraph.domain.value_objects.graph_pattern import GraphPattern

logger = logging.getLogger(__name__)

# Importar funciones de graph_operations de manera lazy para evitar importaciones circulares
# Estas funciones se importan solo cuando se necesitan, no al nivel del módulo
try:
    from ungraph.utils.graph_operations import graph_session, extract_document_structure, create_chunk_relationships
except ImportError as e:
    logger.error("Cannot import graph_operations. Ensure the package is installed or PYTHONPATH includes project root. Original error: %s", e)
    raise


class Neo4jChunkRepository(ChunkRepository):
    """
    Implementación de ChunkRepository usando Neo4j.
    
    Esta implementación:
    - Crea File y Page automáticamente al guardar Chunks
    - Usa el código existente de graph_operations.py
    - Maneja la conexión a Neo4j internamente
    """
    
    def __init__(self, database: str = "neo4j"):
        """
        Inicializa el repositorio.
        
        Args:
            database: Nombre de la base de datos Neo4j (default: "neo4j")
        """
        self.database = database
        self._driver = None
    
    def _get_driver(self) -> GraphDatabase:
        """Obtiene o crea el driver de Neo4j."""
        if self._driver is None:
            self._driver = graph_session()
        return self._driver
    
    def save(self, chunk: Chunk) -> None:
        """
        Guarda un chunk individual en Neo4j.
        
        Crea automáticamente File y Page si no existen.
        """
        self.save_batch([chunk])
    
    def save_batch(self, chunks: List[Chunk]) -> None:
        """
        Guarda múltiples chunks en Neo4j de forma eficiente.
        
        Crea automáticamente File y Page si no existen.
        """
        if not chunks:
            return
        
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                for chunk in chunks:
                    # Extraer datos del chunk
                    filename = chunk.metadata.get('filename', 'unknown')
                    page_number = chunk.metadata.get('page_number', 1)
                    
                    # Convertir embeddings a lista si es necesario
                    embeddings = chunk.embeddings
                    if embeddings is None:
                        embeddings = []
                    
                    session.execute_write(
                        extract_document_structure,
                        filename=filename,
                        page_number=page_number,
                        chunk_id=chunk.id,
                        page_content=chunk.page_content,
                        is_unitary=chunk.is_unitary,
                        embeddings=embeddings,
                        embeddings_dimensions=chunk.embeddings_dimensions or 384,
                        embedding_encoder_info=chunk.embedding_encoder_info or 'unknown',
                        chunk_id_consecutive=chunk.chunk_id_consecutive or 0
                    )
        except ClientError as e:
            logger.error(f"Error saving chunks to Neo4j: {e}", exc_info=True)
            raise
    
    def find_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """
        Busca un chunk por su ID en Neo4j.
        
        Args:
            chunk_id: Identificador único del chunk
        
        Returns:
            La entidad Chunk si se encuentra, None si no existe
        """
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                result = session.execute_read(
                    self._find_chunk_by_id_query,
                    chunk_id=chunk_id
                )
                
                if not result:
                    return None
                
                # Convertir resultado de Neo4j a entidad Chunk
                record = result[0]
                return self._record_to_chunk(record)
        except Exception as e:
            logger.error(f"Error finding chunk by id {chunk_id}: {e}", exc_info=True)
            raise
    
    def _find_chunk_by_id_query(self, tx, chunk_id: str):
        """Query helper para buscar chunk por ID."""
        query = """
        MATCH (c:Chunk {chunk_id: $chunk_id})
        RETURN c.page_content as page_content,
               c.chunk_id as chunk_id,
               c.chunk_id_consecutive as chunk_id_consecutive,
               c.is_unitary as is_unitary,
               c.embeddings as embeddings,
               c.embeddings_dimensions as embeddings_dimensions,
               c.embedding_encoder_info as embedding_encoder_info,
               c.filename as filename,
               c.page_number as page_number
        LIMIT 1
        """
        result = tx.run(query, chunk_id=chunk_id)
        return list(result)
    
    def find_by_filename(self, filename: str) -> List[Chunk]:
        """
        Busca todos los chunks de un archivo específico en Neo4j.
        
        Args:
            filename: Nombre del archivo
        
        Returns:
            Lista de entidades Chunk del archivo
        """
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                result = session.execute_read(
                    self._find_chunks_by_filename_query,
                    filename=filename
                )
                
                # Convertir resultados de Neo4j a entidades Chunk
                chunks = [self._record_to_chunk(record) for record in result]
                return chunks
        except Exception as e:
            logger.error(f"Error finding chunks by filename {filename}: {e}", exc_info=True)
            raise
    
    def _find_chunks_by_filename_query(self, tx, filename: str):
        """Query helper para buscar chunks por filename."""
        query = """
        MATCH (c:Chunk)
        WHERE c.filename = $filename
        RETURN c.page_content as page_content,
               c.chunk_id as chunk_id,
               c.chunk_id_consecutive as chunk_id_consecutive,
               c.is_unitary as is_unitary,
               c.embeddings as embeddings,
               c.embeddings_dimensions as embeddings_dimensions,
               c.embedding_encoder_info as embedding_encoder_info,
               c.filename as filename,
               c.page_number as page_number
        ORDER BY c.chunk_id_consecutive ASC
        """
        result = tx.run(query, filename=filename)
        return list(result)
    
    def _record_to_chunk(self, record) -> Chunk:
        """Convierte un record de Neo4j a entidad Chunk."""
        from ungraph.domain.entities.chunk import Chunk
        
        metadata = {
            'filename': record.get('filename', 'unknown'),
            'page_number': record.get('page_number', 1)
        }
        
        return Chunk(
            id=record.get('chunk_id', ''),
            page_content=record.get('page_content', ''),
            metadata=metadata,
            is_unitary=record.get('is_unitary', False),
            chunk_id_consecutive=record.get('chunk_id_consecutive', 0),
            embeddings=record.get('embeddings'),
            embeddings_dimensions=record.get('embeddings_dimensions'),
            embedding_encoder_info=record.get('embedding_encoder_info')
        )
    
    def save_with_pattern(self, chunks: List[Chunk], pattern: GraphPattern) -> None:
        """
        Guarda chunks usando un patrón específico de grafo.
        
        Si el patrón es FILE_PAGE_CHUNK, usa save_batch() existente (compatibilidad).
        Si es otro patrón, usa PatternService para aplicar el patrón.
        
        Args:
            chunks: Lista de chunks a guardar
            pattern: Patrón de grafo a usar
        
        Raises:
            ValueError: Si el patrón es inválido
            RuntimeError: Si hay un error al guardar
        """
        if not chunks:
            return
        
        # Importar PatternService aquí para evitar dependencia circular
        from ungraph.infrastructure.services.neo4j_pattern_service import Neo4jPatternService
        
        # Si es FILE_PAGE_CHUNK, usar método existente (backward compatibility)
        if pattern.name == "FILE_PAGE_CHUNK":
            logger.info("Using existing save_batch() for FILE_PAGE_CHUNK pattern")
            self.save_batch(chunks)
            return
        
        # Para otros patrones, usar PatternService
        # PatternService maneja su propia sesión, así que solo necesitamos llamarlo
        pattern_service = Neo4jPatternService(database=self.database)
        
        try:
            for chunk in chunks:
                # Convertir chunk a formato de datos para el patrón
                data = self._chunk_to_pattern_data(chunk, pattern)
                
                # Aplicar patrón usando PatternService
                # PatternService.apply_pattern maneja la ejecución internamente
                pattern_service.apply_pattern(pattern, data)
        except Exception as e:
            logger.error(f"Error saving chunks with pattern {pattern.name}: {e}", exc_info=True)
            raise
        finally:
            pattern_service.close()
    
    def _chunk_to_pattern_data(self, chunk: Chunk, pattern: GraphPattern) -> dict:
        """
        Convierte un Chunk a formato de datos compatible con el patrón.
        
        Extrae los datos necesarios del chunk según las propiedades requeridas del patrón.
        """
        data = {}
        
        # Extraer datos comunes del chunk
        filename = chunk.metadata.get('filename', 'unknown')
        page_number = chunk.metadata.get('page_number', 1)
        
        # Mapear datos según el patrón
        for node_def in pattern.node_definitions:
            if node_def.label == "Chunk":
                # Propiedades requeridas de Chunk
                data['chunk_id'] = chunk.id
                data['page_content'] = chunk.page_content
                data['embeddings'] = chunk.embeddings or []
                data['embeddings_dimensions'] = chunk.embeddings_dimensions or 384
                
                # Propiedades opcionales
                if 'is_unitary' in node_def.optional_properties:
                    data['is_unitary'] = chunk.is_unitary
                if 'chunk_id_consecutive' in node_def.optional_properties:
                    data['chunk_id_consecutive'] = chunk.chunk_id_consecutive or 0
                if 'embedding_encoder_info' in node_def.optional_properties:
                    data['embedding_encoder_info'] = chunk.embedding_encoder_info or 'unknown'
            
            elif node_def.label == "File":
                data['filename'] = filename
                # createdAt se maneja automáticamente en el query
            
            elif node_def.label == "Page":
                data['filename'] = filename
                data['page_number'] = page_number
        
        return data
    
    
    def create_chunk_relationships(self) -> None:
        """
        Crea relaciones NEXT_CHUNK entre chunks consecutivos.
        
        Usa el código existente de graph_operations.py.
        """
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                create_chunk_relationships(session)
        except Exception as e:
            logger.error(f"Error creating chunk relationships: {e}", exc_info=True)
            raise
    
    def save_facts(self, facts: List[Fact]) -> None:
        """
        Guarda facts en Neo4j creando nodos Fact y relaciones DERIVED_FROM.
        
        Para cada fact:
        - Crea un nodo Fact con propiedades: id, subject, predicate, object, confidence
        - Crea relación DERIVED_FROM desde Fact hacia Chunk (provenance)
        - Si el object es una entidad mencionada, crea nodo Entity y relación MENTIONS
        
        Args:
            facts: Lista de facts a persistir
        
        Raises:
            ClientError: Si hay un error al guardar en Neo4j
        """
        if not facts:
            return
        
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                session.execute_write(
                    self._save_facts_query,
                    facts=facts
                )
            logger.info(f"Successfully saved {len(facts)} facts to Neo4j")
        except ClientError as e:
            logger.error(f"Error saving facts to Neo4j: {e}", exc_info=True)
            raise
    
    def _save_facts_query(self, tx, facts: List[Fact]):
        """
        Query helper para guardar facts en Neo4j.
        
        Crea nodos Fact y relaciones DERIVED_FROM hacia Chunks.
        También crea nodos Entity para objetos que son entidades nombradas.
        """
        query = """
        UNWIND $facts AS fact_data
        MATCH (chunk:Chunk {chunk_id: fact_data.provenance_ref})
        
        // Crear o actualizar nodo Fact
        MERGE (fact:Fact {fact_id: fact_data.id})
        SET fact.subject = fact_data.subject,
            fact.predicate = fact_data.predicate,
            fact.object = fact_data.object,
            fact.confidence = fact_data.confidence,
            fact.provenance_ref = fact_data.provenance_ref
        
        // Crear relación DERIVED_FROM (provenance)
        MERGE (fact)-[:DERIVED_FROM]->(chunk)
        
        WITH fact, fact_data, chunk
        
        // Si el object NO es un chunk_id existente, crear nodo Entity
        // y relación MENTIONS desde chunk hacia entity
        WHERE NOT EXISTS {
            MATCH (c:Chunk {chunk_id: fact_data.object})
        }
        
        MERGE (entity:Entity {name: fact_data.object})
        ON CREATE SET entity.entity_id = fact_data.object + '_entity',
                      entity.type = 'UNKNOWN'
        
        MERGE (chunk)-[:MENTIONS]->(entity)
        
        RETURN count(fact) as facts_created
        """
        
        # Preparar datos para la query
        facts_data = [
            {
                "id": fact.id,
                "subject": fact.subject,
                "predicate": fact.predicate,
                "object": fact.object,
                "confidence": fact.confidence,
                "provenance_ref": fact.provenance_ref
            }
            for fact in facts
        ]
        
        result = tx.run(query, facts=facts_data)
        return list(result)
    
    def close(self) -> None:
        """Cierra la conexión a Neo4j."""
        if self._driver:
            self._driver.close()
            self._driver = None

