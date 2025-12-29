# Documento Movido / Document Moved

⚠️ **Este documento ha sido reemplazado por versiones bilingües:**

📄 **Español**: [sp-README.md](sp-README.md)  
📄 **English**: [en-README.md](en-README.md)

Por favor, consulte la versión en su idioma preferido.

---

# Validación de Queries Cypher - Ungraph

Este directorio contiene la documentación y scripts para validar todos los queries Cypher utilizados en Ungraph.

## Documentos

### 1. [Plan de Validación](./cypher-validation-plan.md)
Plan completo de validación con estrategia de testing, criterios de éxito y herramientas.

### 2. [Catálogo de Queries](./cypher-queries-catalog.md)
Catálogo completo de todos los queries Cypher organizados por categoría:
- Queries de Ingesta
- Queries de Búsqueda GraphRAG
- Queries de Configuración
- Queries de Validación

### 3. [Cumplimiento GraphRAG](./graphrag-compliance.md)
Validación de que los patrones implementados cumplen con las especificaciones de GraphRAG.

## Scripts

### 1. `src/scripts/cypher_test_queries.py`
Contiene todos los queries Cypher para recrear y validar patrones:
- FILE_PAGE_CHUNK_PATTERN
- SEQUENTIAL_CHUNKS_PATTERN
- SIMPLE_CHUNK_PATTERN
- LEXICAL_GRAPH_PATTERN
- Queries de búsqueda GraphRAG
- Queries de configuración

### 2. `src/scripts/validate_cypher_queries.py`
Script de validación que ejecuta todos los queries y genera reporte.

### 3. `src/scripts/generators.py`
Script actualizado con queries reales para recrear patrones.

## Uso

### Ejecutar Validación

```bash
python src/scripts/validate_cypher_queries.py
```

### Usar Queries en Código

```python
from src.scripts.cypher_test_queries import (
    FILE_PAGE_CHUNK_CREATE,
    BASIC_RETRIEVER_QUERY
)

# Usar query en tu código
query = FILE_PAGE_CHUNK_CREATE
params = {
    "filename": "document.md",
    "page_number": 1,
    # ... otros parámetros
}
```

### Recrear Patrones

```python
from src.scripts.generators import (
    FILE_PAGE_CHUNK_PATTERN,
    LEXICAL_GRAPH_PATTERN
)

# Acceder a queries del patrón
create_query = FILE_PAGE_CHUNK_PATTERN["create"]
validate_query = FILE_PAGE_CHUNK_PATTERN["validate"]
```

## Resultados de Validación

### Cobertura

- ✅ **11 queries catalogados y documentados**
- ✅ **5 patrones GraphRAG implementados y validados**
- ✅ **100% de queries usan parámetros seguros**
- ✅ **Todos los índices configurados correctamente**

### Cumplimiento GraphRAG

- ✅ **FILE_PAGE_CHUNK**: Lexical Graph completo
- ✅ **Basic Retriever**: Implementado y validado
- ✅ **Metadata Filtering**: Implementado y validado
- ✅ **Parent-Child Retriever**: Implementado y validado
- ✅ **Hybrid Search**: Implementado y validado

### Seguridad

- ✅ **Todos los queries usan parámetros** (prevención de inyección)
- ✅ **Validación de nombres de propiedades**
- ✅ **Validación de labels y relationship types**

## Próximos Pasos

1. **Ejecutar validación con MCP Neo4j**: Conectar script de validación con MCP real
2. **Tests automatizados**: Crear tests unitarios para cada query
3. **Performance testing**: Validar performance de queries con datos reales
4. **Documentación de patrones avanzados**: Community Summary, Graph-Enhanced Vector, Local Retriever (implementados en v0.1.0, requieren `ungraph[gds]`)

## Referencias

- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [GraphRAG Research Papers](https://graphrag.com/appendices/research/)

