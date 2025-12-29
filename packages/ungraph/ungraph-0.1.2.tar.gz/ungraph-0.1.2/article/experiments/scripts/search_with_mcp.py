#!/usr/bin/env python
"""
Script de ejemplo para búsqueda avanzada usando MCP y patrones GraphRAG.

Este script demuestra cómo usar los patrones avanzados de búsqueda
con MCP (Model Context Protocol) para validación y ejecución de queries.

Requisitos:
- pip install ungraph[gds]
- Neo4j corriendo
- MCP Neo4j configurado (opcional, para validación)
"""

import argparse
import sys
from pathlib import Path

# Agregar src al path si es necesario
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.configuration import get_settings, configure
from infrastructure.services.neo4j_search_service import Neo4jSearchService
from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService


def validate_query_with_mcp(query: str, params: dict) -> bool:
    """
    Valida un query Cypher usando MCP Neo4j (si está disponible).
    
    Args:
        query: Query Cypher a validar
        params: Parámetros del query
    
    Returns:
        True si el query es válido, False si hay error
    """
    try:
        # Intentar usar MCP Neo4j si está disponible
        from mcp_neo4j_cypher import read_neo4j_cypher
        
        # Validar sintaxis ejecutando el query (read-only)
        result = read_neo4j_cypher(query=query, params=params)
        return True
    except ImportError:
        print("⚠️  MCP Neo4j no disponible, saltando validación")
        return True
    except Exception as e:
        print(f"❌ Error validando query: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Búsqueda avanzada con patrones GraphRAG usando MCP"
    )
    parser.add_argument("query", help="Texto a buscar")
    parser.add_argument(
        "--pattern",
        choices=["basic", "metadata_filtering", "parent_child", "graph_enhanced", "local", "community_summary"],
        default="basic",
        help="Patrón de búsqueda a usar"
    )
    parser.add_argument("--limit", type=int, default=5, help="Número máximo de resultados")
    parser.add_argument("--validate", action="store_true", help="Validar queries con MCP")
    parser.add_argument("--database", default=None, help="Base de datos Neo4j")
    
    args = parser.parse_args()
    
    # Configurar (usar variables de entorno si están disponibles)
    settings = get_settings()
    db_name = args.database or settings.neo4j_database
    
    print(f"🔍 Búsqueda: '{args.query}'")
    print(f"📊 Patrón: {args.pattern}")
    print(f"📁 Base de datos: {db_name}")
    print("-" * 80)
    
    # Crear servicio de búsqueda
    search_service = Neo4jSearchService(database=db_name)
    
    try:
        # Preparar parámetros según el patrón
        kwargs = {}
        
        if args.pattern == "metadata_filtering":
            kwargs["metadata_filters"] = {"filename": "example.md"}
        
        if args.pattern == "graph_enhanced":
            # Generar embedding para graph_enhanced
            embedding_service = HuggingFaceEmbeddingService()
            embedding = embedding_service.generate_embedding(args.query)
            kwargs["query_vector"] = embedding.vector
            kwargs["max_traversal_depth"] = 2
        
        if args.pattern == "local":
            kwargs["community_threshold"] = 3
            kwargs["max_depth"] = 1
        
        if args.pattern == "community_summary":
            kwargs["min_community_size"] = 5
        
        # Ejecutar búsqueda
        results = search_service.search_with_pattern(
            query_text=args.query,
            pattern_type=args.pattern,
            limit=args.limit,
            **kwargs
        )
        
        print(f"✅ Encontrados {len(results)} resultados\n")
        
        # Mostrar resultados
        for i, result in enumerate(results, 1):
            print(f"Resultado {i}:")
            print(f"  Score: {result.score:.4f}")
            print(f"  Chunk ID: {result.chunk_id}")
            print(f"  Contenido: {result.content[:200]}...")
            if result.next_chunk_content:
                print(f"  Contexto adicional: {result.next_chunk_content[:200]}...")
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        search_service.close()


if __name__ == "__main__":
    main()

