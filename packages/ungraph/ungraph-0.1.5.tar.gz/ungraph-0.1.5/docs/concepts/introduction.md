> Documento movido / Document moved

Este documento ahora está disponible en versiones bilingües:

- Español: [sp-introduction.md](sp-introduction.md)
- English: [en-introduction.md](en-introduction.md)

Por favor actualiza tus enlaces y marcadores a una de las versiones anteriores.

Please update your links/bookmarks to one of the above versions.

1. **Cargar documentos** (Markdown, TXT, Word, PDF)
2. **Dividirlos en chunks inteligentes** con recomendaciones automáticas
3. **Generar embeddings** usando modelos de HuggingFace
4. **Persistirlos en un grafo de conocimiento** (Neo4j)
5. **Buscar información** usando búsqueda híbrida (texto + vectorial)

## Concepto Fundamental

Ungraph parte de la premisa de que toda data no estructurada puede organizarse en entidades fundamentales usando un **Lexical Graph**:

```
File → Page → Chunk
```

Con relaciones:
- `File -[:CONTAINS]-> Page`
- `Page -[:HAS_CHUNK]-> Chunk`
- `Chunk -[:NEXT_CHUNK]-> Chunk` (chunks consecutivos)

**¿Qué es un Lexical Graph?** Es una estructura que organiza texto y captura relaciones lingüísticas, facilitando la búsqueda semántica. El patrón `FILE_PAGE_CHUNK` implementa un Lexical Graph que es compatible con patrones de GraphRAG como Basic Retriever y Parent-Child Retriever.

Ver [Lexical Graphs](./lexical-graphs.md) para más detalles.

## Características Principales

### ✅ Pipeline Completo
- Carga de múltiples formatos (Markdown, TXT, Word, PDF)
- Detección automática de encoding
- Limpieza de texto
- Chunking inteligente con recomendaciones
- Generación de embeddings
- Persistencia en Neo4j

### ✅ Búsqueda Avanzada
- Búsqueda por texto (full-text search)
- Búsqueda vectorial (similarity search)
- Búsqueda híbrida (combinación de ambas)
- Patrones GraphRAG avanzados (Parent-Child, Community, etc.)

### ✅ Arquitectura Limpia
- Clean Architecture para mantenibilidad
- Separación clara de responsabilidades
- Fácil de testear y extender
- Código profesional y documentado

### ✅ Sistema de Patrones
- Patrones de grafo configurables
- Patrones predefinidos listos para usar
- Creación de patrones personalizados
- Validación automática

## Casos de Uso

### Caso 1: Documentación Técnica
Convertir documentación técnica en un grafo de conocimiento para búsqueda semántica.

### Caso 2: Investigación Académica
Organizar papers y artículos académicos en un grafo para exploración de conocimiento.

### Caso 3: Knowledge Base Empresarial
Construir una base de conocimiento empresarial a partir de documentos internos.

## Instalación

```bash
pip install ungraph
```

O desde el código fuente:

```bash
git clone https://github.com/tu-usuario/ungraph.git
cd ungraph
pip install -e .
```

## Uso Básico

```python
import ungraph

# 1. Ingerir un documento
chunks = ungraph.ingest_document("documento.md")
print(f"✅ Documento dividido en {len(chunks)} chunks")

# 2. Buscar información
results = ungraph.search("consulta de ejemplo", limit=5)
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")

# 3. Búsqueda híbrida
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.4, 0.6)  # Más peso a búsqueda vectorial
)
```

## Requisitos

- Python 3.12+
- Neo4j 5.x
- Dependencias listadas en `pyproject.toml`

## Referencias

- [README Principal](../../README.md)
- [Guía de Inicio Rápido](../guides/sp-quickstart.md)
- [Arquitectura del Sistema](architecture.md)


