# Guía de Inicio Rápido

Esta guía te ayudará a empezar con Ungraph en minutos.

## Instalación

```bash
pip install ungraph
```

## Configuración Inicial

### Opción 1: Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=tu_contraseña
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Opción 2: Configuración Programática

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="tu_contraseña",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

## Primer Ejemplo: Ingerir un Documento

```python
import ungraph
from pathlib import Path

# Ingerir un documento
chunks = ungraph.ingest_document(
    "mi_documento.md",
    chunk_size=1000,
    chunk_overlap=200
)

print(f"✅ Documento ingerido exitosamente!")
print(f"   Total de chunks: {len(chunks)}")
```

## Segundo Ejemplo: Buscar Información

```python
# Búsqueda simple por texto
results = ungraph.search("computación cuántica", limit=5)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print("---")
```

## Tercer Ejemplo: Búsqueda Híbrida

```python
# Búsqueda híbrida (texto + vectorial)
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.3, 0.7)  # 30% texto, 70% vectorial
)

for result in results:
    print(f"Score combinado: {result.score:.3f}")
    print(f"Contenido: {result.content}")
    
    # Contexto adicional
    if result.previous_chunk_content:
        print(f"Contexto anterior: {result.previous_chunk_content[:100]}...")
    if result.next_chunk_content:
        print(f"Contexto siguiente: {result.next_chunk_content[:100]}...")
    print("=" * 80)
```

## Cuarto Ejemplo: Obtener Recomendaciones de Chunking

```python
# Obtener recomendación de estrategia de chunking
recommendation = ungraph.suggest_chunking_strategy("mi_documento.md")

print(f"Estrategia recomendada: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explicación: {recommendation.explanation}")
print(f"Score de calidad: {recommendation.quality_score:.2f}")
```

## Ejemplo Completo: Pipeline End-to-End

```python
import ungraph
from pathlib import Path

# 1. Configurar (si no usas variables de entorno)
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña"
)

# 2. Obtener recomendación de chunking
recommendation = ungraph.suggest_chunking_strategy("documento.md")
print(f"Usando estrategia: {recommendation.strategy}")

# 3. Ingerir documento con parámetros recomendados
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
print(f"✅ {len(chunks)} chunks creados")

# 4. Buscar información
results = ungraph.hybrid_search(
    "tema de interés",
    limit=5
)

# 5. Procesar resultados
for result in results:
    contexto_completo = ""
    if result.previous_chunk_content:
        contexto_completo += f"[Anterior] {result.previous_chunk_content}\n\n"
    contexto_completo += f"[Principal] {result.content}\n\n"
    if result.next_chunk_content:
        contexto_completo += f"[Siguiente] {result.next_chunk_content}"
    
    print(contexto_completo)
    print("=" * 80)
```

## Siguientes Pasos

- [Guía de Ingesta](sp-ingestion.md) - Aprende más sobre ingesta de documentos
- [Guía de Búsqueda](../guides/search.md) - Explora patrones de búsqueda avanzados
- [Patrones Personalizados](sp-custom-patterns.md) - Crea tus propios patrones
- [Ejemplos Avanzados](../examples/advanced-examples.md) - Casos de uso complejos

## Solución de Problemas

### Error: AuthError al conectar a Neo4j

**Solución:** Verifica que:
1. Neo4j está corriendo
2. Las credenciales son correctas
3. La URI es accesible (puerto 7687 por defecto)

```python
# Verificar configuración
from ungraph.core.configuration import get_settings
settings = get_settings()
print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
```

### Error: UnicodeDecodeError al cargar archivo

**Solución:** El sistema detecta automáticamente el encoding, pero si persiste:

```python
# El sistema intenta automáticamente múltiples encodings:
# utf-8, windows-1252, latin-1, iso-8859-1, cp1252
# Si falla, verifica el archivo manualmente
```

## Referencias

- [README Principal](../../README.md)
- [Documentación de API](../api/sp-public-api.md)
- [Configuración](../api/sp-configuration.md)
