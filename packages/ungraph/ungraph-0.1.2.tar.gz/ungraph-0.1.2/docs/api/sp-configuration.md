# Configuración de Ungraph

Guía completa de configuración de Ungraph.

## Métodos de Configuración

Ungraph soporta dos métodos de configuración:

1. **Variables de Entorno** (recomendado para producción)
2. **Configuración Programática** (útil para desarrollo y scripts)

## Variables de Entorno

### Prefijo

Todas las variables de entorno usan el prefijo `UNGRAPH_`:

```bash
UNGRAPH_NEO4J_URI=...
UNGRAPH_NEO4J_USER=...
UNGRAPH_NEO4J_PASSWORD=...
```

### Variables Disponibles

| Variable | Descripción | Default |
|----------|-------------|---------|
| `UNGRAPH_NEO4J_URI` | URI de conexión a Neo4j | `bolt://localhost:7687` |
| `UNGRAPH_NEO4J_USER` | Usuario de Neo4j | `neo4j` |
| `UNGRAPH_NEO4J_PASSWORD` | Contraseña de Neo4j | (requerido) |
| `UNGRAPH_NEO4J_DATABASE` | Nombre de la base de datos | `neo4j` |
| `UNGRAPH_EMBEDDING_MODEL` | Modelo de embedding | `sentence-transformers/all-MiniLM-L6-v2` |
| `UNGRAPH_STORAGE_PROVIDER` | Proveedor de almacenamiento | `neo4j` |
| `UNGRAPH_INFERENCE_MODE` | Modo de inferencia (`ner` | `llm` | `hybrid`) | `ner` |

### Ejemplo: Archivo `.env`

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=mi_contraseña_segura
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
UNGRAPH_INFERENCE_MODE=ner
```

### Ejemplo: Variables de Entorno en Shell

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="mi_contraseña"
export UNGRAPH_NEO4J_DATABASE="neo4j"
```

## Configuración Programática

### Usar `ungraph.configure()`

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="mi_contraseña",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    inference_mode="ner"  # valores: 'ner' | 'llm' | 'hybrid'
)
```

### Acceder a Configuración

```python
from ungraph.core.configuration import get_settings

settings = get_settings()

print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
print(f"Database: {settings.neo4j_database}")
print(f"Embedding Model: {settings.embedding_model}")
print(f"Inference Mode: {settings.inference_mode}")
```

## Prioridad de Configuración

La configuración se aplica en este orden (mayor prioridad primero):

1. **Configuración programática** (`ungraph.configure()`)
2. **Variables de entorno** (`UNGRAPH_*`)
3. **Valores por defecto**

## Ejemplos de Configuración

### Desarrollo Local

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="dev_password",
    inference_mode="ner"  # baseline v0.1.0
)
```

### Producción con Variables de Entorno

```bash
# En tu servidor o contenedor
export UNGRAPH_NEO4J_URI="bolt://neo4j.production:7687"
export UNGRAPH_NEO4J_PASSWORD="production_password"
export UNGRAPH_INFERENCE_MODE="llm"  # activar inferencia semántica (v0.2+)
```

### Múltiples Bases de Datos

```python
import ungraph

# Base de datos 1
ungraph.configure(neo4j_database="db1")
chunks1 = ungraph.ingest_document("doc1.md", database="db1")

# Base de datos 2
ungraph.configure(neo4j_database="db2")
chunks2 = ungraph.ingest_document("doc2.md", database="db2")
```

## Validación de Configuración

La configuración se valida automáticamente al usar las funciones:

```python
import ungraph

try:
    chunks = ungraph.ingest_document("doc.md")
except ValueError as e:
    print(f"Error de configuración: {e}")
    # Verifica que las variables de entorno estén configuradas
```

## Solución de Problemas

### Error: "Neo4j URI not configured"

**Solución:** Configura la URI:

```python
ungraph.configure(neo4j_uri="bolt://localhost:7687")
```

O usando variable de entorno:

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
```

### Error: "Neo4j password not configured"

**Solución:** Configura la contraseña:

```python
ungraph.configure(neo4j_password="tu_contraseña")
```

O usando variable de entorno:

```bash
export UNGRAPH_NEO4J_PASSWORD="tu_contraseña"
```

### Error: AuthError al conectar

**Solución:** Verifica las credenciales:

```python
from ungraph.core.configuration import get_settings

settings = get_settings()
print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
# La contraseña no se muestra por seguridad
```

## Notas sobre `inference_mode`

- `ner` (default): usa spaCy NER para extracción de entidades y facts básicos de mención. Recomendado en v0.1.0.
- `llm`: activa la inferencia semántica (relaciones tipadas) con LLMs. Disponible a partir de v0.2.0.
- `hybrid`: combina NER + LLM con estrategias de coste/latencia. Disponible a partir de v0.2.0.

Si se establece `llm` o `hybrid` antes de que los servicios correspondientes estén disponibles, las funciones de inferencia devolverán un error de configuración o caerán al modo `ner` (según la implementación).

## Referencias

- [Guía de Inicio Rápido](../guides/sp-quickstart.md)
- [API Pública](sp-public-api.md)
