import os
import ast
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


# DB Connection
def graph_session() -> GraphDatabase:
    """
    Creates and returns a connection session to the Neo4j database.

    This function uses configuration from src.core.configuration (centralized).

    Returns:
        GraphDatabase: A Neo4j database driver that allows performing operations
        on the database.

    Raises:
        ValueError: If NEO4J_URI or NEO4J_PASSWORD are not set.
        RuntimeError: If an error occurs while trying to create the database session.
    """
    from src.core.configuration import get_settings
    
    settings = get_settings()
    URI = settings.neo4j_uri
    USER = settings.neo4j_user
    PASSWORD = settings.neo4j_password

    if not URI or not PASSWORD:
        raise ValueError(
            "NEO4J_URI and NEO4J_PASSWORD must be set. "
            "Use ungraph.configure() or set environment variables.\n"
            "Example: ungraph.configure(neo4j_uri='bolt://localhost:7687', neo4j_password='your_password')"
        )
    
    AUTH = (USER, PASSWORD)

    try:
        logger.info(f"Connecting to Neo4j at {URI} with user {USER}")
        driver = GraphDatabase.driver(URI, auth=AUTH)
        driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j")
        return driver
    except Exception as e:
        error_msg = (
            f"Failed to create a graph session: {e}\n"
            f"URI: {URI}\n"
            f"User: {USER}\n"
            "Please check:\n"
            "1. Neo4j is running\n"
            "2. Credentials are correct\n"
            "3. URI is accessible"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e




## PROCESAMIENTO DE DOCUMENT DATA OBJECT A GRAFO.
# Función para extraer estructura de documento
def extract_document_structure(tx, 
                               filename, 
                               page_number, 
                               chunk_id, 
                               page_content, 
                               is_unitary, 
                               embeddings, 
                               embeddings_dimensions, 
                               embedding_encoder_info,
                               chunk_id_consecutive):
    """
    Extrae y persiste la estructura FILE-PAGE-CHUNK en Neo4j.
    
    Esta función implementa el patrón básico de estructura del grafo:
    File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
    
    TODO: CREAR EL FUNCIONAMIENTO DE DOD PARA QUE SIRVA CON LO QUE SE LEE EN EL DCUMENTO DE DOCLING.
    
    NOTA: Patrón actual hardcodeado. Para implementar patrones configurables:
    
    ```python
    # Pseudo-implementación de sistema de patrones:
    
    # 1. Definir Value Object para patrones
    @dataclass(frozen=True)
    class GraphPattern:
        name: str
        node_types: List[str]  # ["File", "Page", "Chunk"]
        relationships: Dict[str, List[str]]  # {"File": ["CONTAINS"], "Page": ["HAS_CHUNK"]}
        node_properties: Dict[str, Dict[str, Any]]  # Propiedades por tipo de nodo
    
    # 2. Patrón básico actual
    BASIC_PATTERN = GraphPattern(
        name="FILE_PAGE_CHUNK",
        node_types=["File", "Page", "Chunk"],
        relationships={
            "File": ["CONTAINS"],
            "Page": ["HAS_CHUNK"],
            "Chunk": ["NEXT_CHUNK"]
        },
        node_properties={
            "File": {"filename": str, "createdAt": int},
            "Page": {"filename": str, "page_number": int},
            "Chunk": {"chunk_id": str, "page_content": str, ...}
        }
    )
    
    # 3. Función genérica que usa el patrón
    def extract_document_structure_with_pattern(
        tx, pattern: GraphPattern, **data
    ):
        # Generar query Cypher dinámicamente basado en el patrón
        query = generate_cypher_from_pattern(pattern, data)
        return tx.run(query, **data)
    
    # 4. Permitir pasar patrón como parámetro
    def ingest_document(file_path, pattern: GraphPattern = BASIC_PATTERN):
        # Usar patrón para estructurar el grafo
        ...
    ```
    """
    try:
        query = """
                MERGE (f:File {filename: $filename})
                ON CREATE SET f.createdAt = timestamp()

                MERGE (p:Page {filename: $filename, page_number: toInteger($page_number)})

                MERGE (c:Chunk {chunk_id: $chunk_id})
                ON CREATE SET c.page_content = $page_content,
                              c.is_unitary = $is_unitary,
                              c.embeddings = $embeddings, 
                              c.embeddings_dimensions = toInteger($embeddings_dimensions),
                              c.embedding_encoder_info = $embedding_encoder_info,
                              c.chunk_id_consecutive = toInteger($chunk_id_consecutive)

                MERGE (f)-[:CONTAINS]->(p)
                MERGE (p)-[:HAS_CHUNK]->(c)

            """
        result = tx.run(query, 
                        filename=filename, 
                        page_number=page_number,
                        chunk_id=chunk_id,
                        page_content=page_content,
                        is_unitary=is_unitary,
                        embeddings=embeddings,
                        embeddings_dimensions=embeddings_dimensions,
                        embedding_encoder_info=embedding_encoder_info,
                        chunk_id_consecutive=chunk_id_consecutive)
        return result
    except ClientError as e:
        logger.error("Database error", exc_info=True)
        tx.rollback()
        raise



# Creo las relaciones entre chunks consecutivos.
def create_chunk_relationships(session):
    """Crear relaciones NEXT_CHUNK entre chunks consecutivos"""
    join_chunks_query = """
    MATCH (c1:Chunk),(c2:Chunk)
    WHERE c1.chunk_id_consecutive + 1 = c2.chunk_id_consecutive
    MERGE (c1)-[:NEXT_CHUNK]->(c2)
    """
    try:
        session.execute_write(lambda tx: tx.run(join_chunks_query))
        logger.info("Chunk relationships created successfully")
    except Exception as e:
        logger.exception("Error creating chunk relationships: %s", e)
        raise



#  Valido que el DataFrame tenga la estructura correcta.
def validate_dataframe(df, expected_dim=384):
    """Validar que el DataFrame tenga la estructura correcta"""
    required_columns = [
        'filename', 'page_number', 'chunk_id', 'page_content',
        'is_unitary', 'embeddings', 'embeddings_dimensions',
        'embedding_encoder_info', 'chunk_id_consecutive'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Validar dimensiones de embeddings
    # Aqui podemos poner las demas dimensiones de los modelo, y ligarlos a la columna de encoder_info.
    if not all(len(emb) == expected_dim for emb in df['embeddings']):
        raise ValueError(f"All embeddings must have {expected_dim} dimensions")
    
    # Validar que chunk_id_consecutive sea secuencial
    # 
    expected_range = range(1, len(df) + 1)
    if not all(df['chunk_id_consecutive'] == expected_range):
        raise ValueError("chunk_id_consecutive must be sequential starting from 1")
    
    return True



# Configuración de índices avanzados, para la búsqueda por contenido y por vector.
def setup_advanced_indexes(session):
    """Configuración de índices avanzados"""
    try:
        # Índice vectorial mejorado
        vector_index_query = """
        CALL db.index.vector.createNodeIndex(
            'chunk_embeddings',           // nombre del índice
            'Chunk',                      // label del nodo
            'embeddings',                 // propiedad que contiene el vector
            384,                          // dimensiones del vector
            'cosine'                      // similitud por coseno
        )
        """
        
        # Índice de texto completo mejorado
        fulltext_index_query = """
        CREATE FULLTEXT INDEX chunk_content IF NOT EXISTS
        FOR (c:Chunk)
        ON EACH [c.page_content]
        OPTIONS {
            indexConfig: {
                `fulltext.analyzer`: 'spanish',
                `fulltext.eventually_consistent`: false
            }
        }
        """
        # Índice regular para búsquedas por chunk_id_consecutive
        regular_index_query = """
        CREATE INDEX chunk_consecutive_idx IF NOT EXISTS
        FOR (c:Chunk)
        ON (c.chunk_id_consecutive)
        """
        

        try:
            session.execute_write(lambda tx: tx.run(regular_index_query))
            logger.info("Regular index created successfully")
        except Exception as e:
            logger.exception("Regular index creation message: %s", e)
            
        try:
            session.execute_write(lambda tx: tx.run(vector_index_query))
            logger.info("Vector index created successfully")
        except Exception as e:
            if "An equivalent index already exists" not in str(e):
                logger.exception("Error creating vector index: %s", e)
                raise e
            logger.info("Vector index already exists")

        try:
            session.execute_write(lambda tx: tx.run(fulltext_index_query))
            logger.info("Full-text index created successfully")
        except Exception as e:
            logger.exception("Full-text index creation message: %s", e)

    except Exception as e:
        print(f"Error in index setup: {e}")



# Tratamiento de columnas para añadir secuencialidad y tipo de dato
def colummn_pretreatment(df):
    # Se les da el formato necesario, esto lo peudo llevar al momento en que se escribe la data en el modulo de ingestión
    df["embeddings"] = df["embeddings"].apply(ast.literal_eval)
    df['chunk_id_consecutive'] = range(1, len(df) + 1)
    return df


# Función para centralizar  el proceso de ingestión de datos al grafo.
def process_with_neo4j(df, batch_size=100, target_database="neo4j"):
    ''' 
    Función que busca:
    1. Configurar los índices en la base de datos.
    2. Validar la idoneidad del dataframe
    3. Procesar en lotes los chunks del texto.
    3.1 Cada lote procesarlo con el query que facilita extraer la extructura del texto.
    4. Una vez creado, populamos con relaciones consecutivas.
    
    '''
    with graph_session() as driver:
        with driver.session(database = target_database) as session:
            # Configurar índices
            setup_advanced_indexes(session)
            
            # Validar datos
            if validate_dataframe(df):
            
                # Procesar chunks en lotes
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i + batch_size]
                    total_batches = (len(df) + batch_size - 1) // batch_size
                    logger.info("Processing batch %d of %d", i // batch_size + 1, total_batches)

                    # Expected default embedding dimension (can be parameterized in the future)
                    embeddings_expected_dim = 384

                    batch.apply(
                        lambda row: session.execute_write(
                            extract_document_structure,
                            filename=row['filename'],
                            page_number=int(row['page_number']),
                            chunk_id=row['chunk_id'],
                            page_content=row['page_content'],
                            is_unitary=bool(row.get('is_unitary', False)),
                            embeddings=row['embeddings'],
                            embeddings_dimensions=int(row.get('embeddings_dimensions', embeddings_expected_dim)),
                            embedding_encoder_info=row.get('embedding_encoder_info', 'unknown'),
                            chunk_id_consecutive=int(row['chunk_id_consecutive'])
                        ),
                        axis=1
                    )

                # Crear relaciones entre chunks consecutivos
                create_chunk_relationships(session)
            else:
                logger.error("Data validation failed for DataFrame")
                raise ValueError("Data validation failed for provided DataFrame")



