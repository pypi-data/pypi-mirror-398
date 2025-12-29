# Documento movido / Moved document

Este documento fue dividido en versiones bilingües y movido.

- Versión en español: [sp-ingestion.md](sp-ingestion.md)
- English version: [en-ingestion.md](en-ingestion.md)

Por favor, usa las nuevas rutas según el idioma deseado.

## Conceptos Básicos

### Flujo de Ingesta

```
Archivo → Documento → Chunks → Embeddings → Grafo Neo4j
```

1. **Cargar archivo**: Se carga el archivo usando `DocumentLoaderService`
2. **Limpiar texto**: Opcionalmente se limpia el texto usando `TextCleaningService`
3. **Dividir en chunks**: Se divide el documento en chunks usando `ChunkingService`
4. **Generar embeddings**: Se generan embeddings para cada chunk usando `EmbeddingService`
5. **Persistir en grafo**: Se guarda en Neo4j usando `ChunkRepository`

## Uso Básico

### Ingerir un Solo Documento

```python
import ungraph

# Ingerir documento con parámetros por defecto
chunks = ungraph.ingest_document("mi_documento.md")

print(f"✅ Documento ingerido: {len(chunks)} chunks creados")
```

### Parámetros de Ingesta

```python
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=1000,        # Tamaño de cada chunk
    chunk_overlap=200,      # Solapamiento entre chunks
    clean_text=True,        # Limpiar texto antes de procesar
    database="neo4j",       # Base de datos Neo4j (opcional)
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # Modelo de embedding
)
```

## Obtener Recomendaciones de Chunking

Ungraph puede analizar tu documento y recomendar la mejor estrategia de chunking:

```python
import ungraph

# Obtener recomendación
recommendation = ungraph.suggest_chunking_strategy("documento.md")

print(f"Estrategia recomendada: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explicación: {recommendation.explanation}")
print(f"Score de calidad: {recommendation.quality_score:.2f}")

# Usar la recomendación
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
```

## Formatos Soportados

### Markdown (.md)

```python
chunks = ungraph.ingest_document("documento.md")
```

### Texto Plano (.txt)

```python
chunks = ungraph.ingest_document("documento.txt")
```

El sistema detecta automáticamente el encoding del archivo (UTF-8, Windows-1252, Latin-1, etc.).

### Word (.docx)

```python
chunks = ungraph.ingest_document("documento.docx")
```

### PDF (.pdf)

```python
chunks = ungraph.ingest_document("documento.pdf")
```

El sistema usa `langchain-docling` (IBM Docling) para extraer texto y metadatos de PDFs, incluyendo información sobre estructura del documento, tablas e imágenes.

## Ejemplo Completo

```python
import ungraph
from pathlib import Path

# 1. Configurar (si no usas variables de entorno)
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña"
)

# 2. Obtener recomendación
recommendation = ungraph.suggest_chunking_strategy("documento.md")
print(f"Usando: {recommendation.strategy}")

# 3. Ingerir con parámetros recomendados
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap,
    clean_text=True
)

# 4. Verificar resultados
print(f"✅ {len(chunks)} chunks creados")
for i, chunk in enumerate(chunks[:3], 1):  # Mostrar primeros 3
    print(f"\nChunk {i}:")
    print(f"  ID: {chunk.id}")
    print(f"  Contenido: {chunk.page_content[:100]}...")
```

## Ingerir Múltiples Documentos

```python
import ungraph
from pathlib import Path

# Lista de archivos a ingerir
archivos = [
    "doc1.md",
    "doc2.txt",
    "doc3.docx",
    "doc4.pdf"
]

for archivo in archivos:
    try:
        chunks = ungraph.ingest_document(archivo)
        print(f"✅ {archivo}: {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error con {archivo}: {e}")
```

## Estructura del Grafo Creado

Después de ingerir, el grafo tiene esta estructura:

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                    Chunk -[:NEXT_CHUNK]-> Chunk
```

**Nodos:**
- **File**: Representa el archivo físico
  - Propiedades: `filename`, `createdAt`
- **Page**: Representa una página dentro del archivo
  - Propiedades: `filename`, `page_number`
- **Chunk**: Representa un fragmento de texto
  - Propiedades: `chunk_id`, `page_content`, `embeddings`, `embeddings_dimensions`
  - Opcionales: `is_unitary`, `chunk_id_consecutive`, `embedding_encoder_info`

**Relaciones:**
- `File -[:CONTAINS]-> Page`: Un archivo contiene páginas
- `Page -[:HAS_CHUNK]-> Chunk`: Una página tiene chunks
- `Chunk -[:NEXT_CHUNK]-> Chunk`: Chunks consecutivos están relacionados

## Solución de Problemas

### Error: UnicodeDecodeError

**Problema:** El archivo tiene un encoding diferente a UTF-8.

**Solución:** El sistema detecta automáticamente el encoding. Si persiste el error, verifica el archivo manualmente.

### Error: AuthError al conectar a Neo4j

**Problema:** Las credenciales de Neo4j son incorrectas.

**Solución:** Verifica las variables de entorno o la configuración programática:

```python
from ungraph.core.configuration import get_settings
settings = get_settings()
print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
```

### Error: Documento muy grande

**Problema:** El documento es demasiado grande para procesar de una vez.

**Solución:** Considera dividir el documento manualmente o usar un `chunk_size` más pequeño.

## Referencias

- [Guía de Inicio Rápido](quickstart.md)
- [API Pública](../api/sp-public-api.md)
- [Patrones de Grafo](../concepts/graph-patterns.md)




