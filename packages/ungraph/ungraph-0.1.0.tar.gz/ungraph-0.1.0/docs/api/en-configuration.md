# Ungraph Configuration

Complete guide to configuring Ungraph.

## Configuration Methods

Ungraph supports two methods:

1. **Environment Variables** (recommended for production)
2. **Programmatic Configuration** (useful for development and scripts)

## Environment Variables

### Prefix

All env vars use the `UNGRAPH_` prefix:

```bash
UNGRAPH_NEO4J_URI=...
UNGRAPH_NEO4J_USER=...
UNGRAPH_NEO4J_PASSWORD=...
```

### Available Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UNGRAPH_NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `UNGRAPH_NEO4J_USER` | Neo4j user | `neo4j` |
| `UNGRAPH_NEO4J_PASSWORD` | Neo4j password | (required) |
| `UNGRAPH_NEO4J_DATABASE` | Database name | `neo4j` |
| `UNGRAPH_EMBEDDING_MODEL` | Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| `UNGRAPH_STORAGE_PROVIDER` | Storage provider | `neo4j` |
| `UNGRAPH_INFERENCE_MODE` | Inference mode (`ner` | `llm` | `hybrid`) | `ner` |

### Example: `.env` file

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=my_secure_password
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
UNGRAPH_INFERENCE_MODE=ner
```

### Example: Shell env vars

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="my_password"
export UNGRAPH_NEO4J_DATABASE="neo4j"
```

## Programmatic Configuration

### Using `ungraph.configure()`

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="my_password",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    inference_mode="ner"  # values: 'ner' | 'llm' | 'hybrid'
)
```

### Access Settings

```python
from ungraph.core.configuration import get_settings

settings = get_settings()

print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
print(f"Database: {settings.neo4j_database}")
print(f"Embedding Model: {settings.embedding_model}")
print(f"Inference Mode: {settings.inference_mode}")
```

## Configuration Priority

Applied in this order (highest priority first):

1. **Programmatic config** (`ungraph.configure()`)
2. **Environment variables** (`UNGRAPH_*`)
3. **Defaults**

## Configuration Examples

### Local Development

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="dev_password",
    inference_mode="ner"
)
```

### Production with Env Vars

```bash
export UNGRAPH_NEO4J_URI="bolt://neo4j.production:7687"
export UNGRAPH_NEO4J_PASSWORD="production_password"
export UNGRAPH_INFERENCE_MODE="llm"
```

### Multiple Databases

```python
import ungraph

# Database 1
ungraph.configure(neo4j_database="db1")
chunks1 = ungraph.ingest_document("doc1.md", database="db1")

# Database 2
ungraph.configure(neo4j_database="db2")
chunks2 = ungraph.ingest_document("doc2.md", database="db2")
```

## Troubleshooting

### Error: "Neo4j URI not configured"

**Solution:** Configure the URI:

```python
ungraph.configure(neo4j_uri="bolt://localhost:7687")
```

Or via env var:

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
```

### Error: "Neo4j password not configured"

**Solution:** Configure the password:

```python
ungraph.configure(neo4j_password="your_password")
```

Or via env var:

```bash
export UNGRAPH_NEO4J_PASSWORD="your_password"
```

### Error: AuthError when connecting

**Solution:** Verify credentials:

```python
from ungraph.core.configuration import get_settings

settings = get_settings()
print(f"URI: {settings.neo4j_uri}")
print(f"User: {settings.neo4j_user}")
# Password not printed for security
```

## Notes on `inference_mode`

- `ner` (default): uses spaCy NER for entity extraction and basic mention facts. Recommended in v0.1.0.
- `llm`: enables semantic inference (typed relationships) with LLMs. Available from v0.2.0.
- `hybrid`: combines NER + LLM with cost/latency strategies. Available from v0.2.0.

If `llm` or `hybrid` is set before required services exist, inference functions will error or fall back to `ner` depending on implementation.

## References

- [Quickstart Guide](../guides/en-quickstart.md)
- [Public API](en-public-api.md)
