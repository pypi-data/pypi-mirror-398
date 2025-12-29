"""
Funciones de visualización de grafos para notebooks.

Este módulo proporciona funciones para visualizar diferentes patrones de grafos
usando yFiles for Jupyter.
"""

from typing import Optional
from neo4j import GraphDatabase

try:
    from yfiles_jupyter_graphs_for_neo4j import Neo4jGraphWidget
except ImportError:
    Neo4jGraphWidget = None


def _check_yfiles_installed():
    """Verifica que yfiles-jupyter-graphs-for-neo4j esté instalado."""
    if Neo4jGraphWidget is None:
        raise ImportError(
            "yfiles-jupyter-graphs-for-neo4j no está instalado. "
            "Instalar con: pip install yfiles-jupyter-graphs-for-neo4j"
        )


def visualize_file_page_chunk_pattern(
    driver: GraphDatabase,
    limit: int = 50,
    filename: Optional[str] = None
) -> None:
    """
    Visualiza el patrón FILE_PAGE_CHUNK.
    
    Muestra la estructura: File -> Page -> Chunk con relaciones NEXT_CHUNK.
    
    Args:
        driver: Driver de Neo4j
        limit: Número máximo de nodos a visualizar
        filename: Filename opcional para filtrar por archivo específico
    """
    _check_yfiles_installed()
    
    # Sanitizar filename para evitar inyección Cypher
    if filename:
        # Escapar comillas simples en el filename
        filename_escaped = filename.replace("'", "\\'")
        query = f"""
        MATCH (f:File {{filename: '{filename_escaped}'}})-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
        OPTIONAL MATCH (c)-[r:NEXT_CHUNK]->(c2:Chunk)
        RETURN f, p, c, r, c2
        LIMIT {limit}
        """
    else:
        query = f"""
        MATCH (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
        OPTIONAL MATCH (c)-[r:NEXT_CHUNK]->(c2:Chunk)
        RETURN f, p, c, r, c2
        LIMIT {limit}
        """
    
    widget = Neo4jGraphWidget(driver, query)
    display(widget)


def visualize_simple_chunk_pattern(
    driver: GraphDatabase,
    limit: int = 50,
    filename: Optional[str] = None
) -> None:
    """
    Visualiza el patrón SIMPLE_CHUNK (solo chunks).
    
    Args:
        driver: Driver de Neo4j
        limit: Número máximo de nodos a visualizar
        filename: Filename opcional para filtrar por archivo específico
    """
    _check_yfiles_installed()
    
    if filename:
        filename_escaped = filename.replace("'", "\\'")
        query = f"""
        MATCH (c:Chunk)
        WHERE c.source_file = '{filename_escaped}' OR c.metadata.filename = '{filename_escaped}'
        RETURN c
        LIMIT {limit}
        """
    else:
        query = f"""
        MATCH (c:Chunk)
        RETURN c
        LIMIT {limit}
        """
    
    widget = Neo4jGraphWidget(driver, query)
    display(widget)


def visualize_lexical_graph_pattern(
    driver: GraphDatabase,
    limit: int = 50,
    filename: Optional[str] = None
) -> None:
    """
    Visualiza un patrón de grafo léxico.
    
    Args:
        driver: Driver de Neo4j
        limit: Número máximo de nodos a visualizar
        filename: Filename opcional para filtrar por archivo específico
    """
    _check_yfiles_installed()
    
    if filename:
        filename_escaped = filename.replace("'", "\\'")
        query = f"""
        MATCH (f:File {{filename: '{filename_escaped}'}})-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
        OPTIONAL MATCH (c)-[r:NEXT_CHUNK|SIMILAR_TO|RELATED_TO]->(c2:Chunk)
        RETURN f, p, c, r, c2
        LIMIT {limit}
        """
    else:
        query = f"""
        MATCH (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
        OPTIONAL MATCH (c)-[r:NEXT_CHUNK|SIMILAR_TO|RELATED_TO]->(c2:Chunk)
        RETURN f, p, c, r, c2
        LIMIT {limit}
        """
    
    widget = Neo4jGraphWidget(driver, query)
    display(widget)


def visualize_hierarchical_pattern(
    driver: GraphDatabase,
    limit: int = 50,
    filename: Optional[str] = None
) -> None:
    """
    Visualiza un patrón jerárquico (Document -> Section -> Chunk).
    
    Args:
        driver: Driver de Neo4j
        limit: Número máximo de nodos a visualizar
        filename: Filename opcional para filtrar por archivo específico
    """
    _check_yfiles_installed()
    
    if filename:
        filename_escaped = filename.replace("'", "\\'")
        query = f"""
        MATCH (d:Document {{filename: '{filename_escaped}'}})-[:HAS_SECTION]->(s:Section)-[:HAS_CHUNK]->(c:Chunk)
        OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(sub:Subsection)-[:HAS_CHUNK]->(c2:Chunk)
        RETURN d, s, sub, c, c2
        LIMIT {limit}
        """
    else:
        query = f"""
        MATCH (d:Document)-[:HAS_SECTION]->(s:Section)-[:HAS_CHUNK]->(c:Chunk)
        OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(sub:Subsection)-[:HAS_CHUNK]->(c2:Chunk)
        RETURN d, s, sub, c, c2
        LIMIT {limit}
        """
    
    widget = Neo4jGraphWidget(driver, query)
    display(widget)


def visualize_sequential_chunks_pattern(
    driver: GraphDatabase,
    limit: int = 50,
    filename: Optional[str] = None
) -> None:
    """
    Visualiza un patrón de chunks secuenciales con relaciones NEXT_CHUNK.
    
    Args:
        driver: Driver de Neo4j
        limit: Número máximo de nodos a visualizar
        filename: Filename opcional para filtrar por archivo específico
    """
    _check_yfiles_installed()
    
    if filename:
        filename_escaped = filename.replace("'", "\\'")
        query = f"""
        MATCH (c1:Chunk)-[r:NEXT_CHUNK*1..3]->(c2:Chunk)
        WHERE c1.source_file = '{filename_escaped}' OR c1.metadata.filename = '{filename_escaped}'
        RETURN c1, r, c2
        LIMIT {limit}
        """
    else:
        query = f"""
        MATCH (c1:Chunk)-[r:NEXT_CHUNK*1..3]->(c2:Chunk)
        RETURN c1, r, c2
        LIMIT {limit}
        """
    
    widget = Neo4jGraphWidget(driver, query)
    display(widget)


def visualize_pattern_structure(
    driver: GraphDatabase,
    pattern_name: str,
    limit: int = 50
) -> None:
    """
    Visualiza la estructura de un patrón específico.
    
    Args:
        driver: Driver de Neo4j
        pattern_name: Nombre del patrón a visualizar
        limit: Número máximo de nodos a visualizar
    """
    _check_yfiles_installed()
    
    pattern_name_escaped = pattern_name.replace("'", "\\'")
    query = f"""
    MATCH (n)
    WHERE n.pattern = '{pattern_name_escaped}' OR n.pattern_name = '{pattern_name_escaped}'
    OPTIONAL MATCH (n)-[r]->(m)
    WHERE m.pattern = '{pattern_name_escaped}' OR m.pattern_name = '{pattern_name_escaped}'
    RETURN n, r, m
    LIMIT {limit}
    """
    
    widget = Neo4jGraphWidget(driver, query)
    display(widget)


def visualize_custom_query(
    driver: GraphDatabase,
    query: str,
    parameters: Optional[dict] = None
) -> None:
    """
    Visualiza un grafo usando una query Cypher personalizada.
    
    Args:
        driver: Driver de Neo4j
        query: Query Cypher personalizada (debe tener valores interpolados, no parámetros)
        parameters: Parámetros opcionales (no se usan, la query debe tener valores interpolados)
    """
    _check_yfiles_installed()
    
    # Nota: Neo4jGraphWidget no acepta parámetros, así que la query debe tener
    # los valores interpolados directamente. El usuario es responsable de sanitizar.
    widget = Neo4jGraphWidget(driver, query)
    display(widget)


def display(widget):
    """Wrapper para display que funciona en Jupyter."""
    try:
        from IPython.display import display as ipython_display
        ipython_display(widget)
    except ImportError:
        # Si no estamos en Jupyter, simplemente retornamos el widget
        return widget

