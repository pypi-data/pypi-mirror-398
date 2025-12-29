
import os
from neo4j.exceptions import ClientError
from .graph_operations import graph_session
import logging

logger = logging.getLogger(__name__)
from neo4j import GraphDatabase



#------------------- GRAPH RAG OPERATIONS -------------


# Búsqueda por contenido.	
def text_search(session, query_text, limit=5):
    """
    Realizar búsqueda por texto usando el índice full-text
    """
    search_query = """
    CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
    YIELD node, score
    RETURN node.page_content as content, score
    ORDER BY score DESC
    LIMIT $limit
    """
    
    result = session.run(search_query, query_text=query_text, limit=limit)
    return [(record["content"], record["score"]) for record in result]



# Búsqueda combinada de texto y vectorial.
def hybrid_search(session, query_text, query_vector, weights=(0.3, 0.7), top_k=5):
    """
    Búsqueda combinada de texto y vectorial
    """
    query = """
    // Búsqueda fulltext
    CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
    YIELD node as text_node, score as text_score
    
    // Combinar con búsqueda vectorial
    CALL {
        WITH text_node
        CALL db.index.vector.queryNodes('chunk_embeddings', toInteger($top_k), $query_vector)
        YIELD node as vec_node, score as vec_score
        WHERE text_node = vec_node
        RETURN vec_node, vec_score
    }
    
    // Calcular score combinado
    WITH text_node as node, text_score, vec_score,
         (text_score * $text_weight + vec_score * $vector_weight) as combined_score
    
    // Obtener contexto
    OPTIONAL MATCH (node)<-[:NEXT_CHUNK]-(prev)
    OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next)
    
    RETURN {
        score: combined_score,
        central_node_content: node.page_content,
        central_node_chunk_id: node.chunk_id,
        central_node_chunk_id_consecutive: node.chunk_id_consecutive,
        surrounding_context: {
            previous_chunk_node_content: prev.page_content,
            previous_chunk_id: prev.chunk_id_consecutive,   
            next_chunk_node_content: next.page_content,
            next_chunk_id: next.chunk_id_consecutive
        }
    } as result
    ORDER BY combined_score DESC
    LIMIT $top_k
    """
    

    
    results = session.run(query,
                         query_text=query_text,
                         query_vector=query_vector,
                         text_weight=weights[0],
                         vector_weight=weights[1],
                         top_k=top_k)
    
    return [record["result"] for record in results]



# Función de alto nivel para buscar en el documento, Ligada a Hybrid Search.
def search_document(query_text, model="all-MiniLM-L6-v2", verbose = False):
    """
    Función de alto nivel para buscar en el documento
    ToDo: Mejorar a documentación
    """
    try:
        # Importar sentence-transformers para generar embeddings
        from sentence_transformers import SentenceTransformer
        
        # Cargar modelo y generar embedding para la consulta
        encoder = SentenceTransformer(model)
        query_vector = encoder.encode(query_text)
        # Asegurarse de que el vector sea una lista de flotantes
        query_vector = [float(x) for x in query_vector.tolist()]
        
     

        driver = graph_session() 
        with driver.session(database="knowledge") as session:
            # Realizar búsqueda híbrida
            results = hybrid_search(
                session=session,
                query_text=query_text,
                query_vector=query_vector,
                weights=(0.3, 0.7),
                top_k=5
            )
            
            if verbose:
                # Formatear y mostrar resultados
                for i, result in enumerate(results, 1):
                    # Cambiar el formato de salida
                    logger.info("Resultado %d:", i)
                    logger.info("  Score: %.4f", result['score'])
                    logger.info("  Contexto anterior: %s", result['surrounding_context']['previous_chunk_node_content'] or 'No disponible')
                    logger.info("  Contenido: %s", result['central_node_content'])
                    logger.info("  Contexto siguiente: %s", result['surrounding_context']['next_chunk_node_content'] or 'No disponible')
                    logger.info("  Chunk ID: %s", result['central_node_chunk_id'])
                    logger.info("%s", "="*80)
                
    except Exception as e:
        logger.exception("Error durante la búsqueda: %s", str(e))
        raise
    finally:
        if 'driver' in locals():
            driver.close()
        return results
    



def gather_surrounding_context(primordial_context):
    # Inicializar un diccionario para almacenar los subtextos
    surrounding_context = {}

    # Concatenar cada elemento en el orden: contenido previo, central, siguiente
    for index, content in enumerate(primordial_context, start=1):  # Comenzar el índice en 1
        subtext = []  # Inicializar una lista para el subtexto actual
        subtext.append(content['surrounding_context']['previous_chunk_node_content'])  # Contenido previo
        subtext.append(content['central_node_content'])                                   # Contenido central
        subtext.append(content['surrounding_context']['next_chunk_node_content'])        # Contenido siguiente
        
        # Unir los textos del subtexto actual y agregarlo al diccionario con el índice
        # Filtro si son None
        surrounding_context[f"subtext_{index}"] = "\n".join(filter(None, subtext))
    
    return surrounding_context
