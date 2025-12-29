# Example Notebooks

Jupyter notebooks available to learn and test Ungraph.

## Available Notebooks

### 1. Using Ungraph Library

**Location:** `src/notebooks/1. Using Ungraph Library.ipynb`

**Contents:**
- Neo4j configuration
- Getting chunking recommendations
- Document ingestion (Markdown, TXT, Word, PDF)
- Text search
- Hybrid search
- End-to-end pipeline

**Usage:**
```bash
jupyter notebook src/notebooks/1.\ Using\ Ungraph\ Library.ipynb
```

### 2. Testing Graph Patterns

**Location:** `src/notebooks/2. Testing Graph Patterns.ipynb`

**Contents:**
- Value Objects (NodeDefinition, RelationshipDefinition, GraphPattern)
- Predefined patterns (FILE_PAGE_CHUNK_PATTERN)
- PatternService (validation and Cypher generation)
- Creating custom patterns
- Systematic tests of all functionality

**Usage:**
```bash
jupyter notebook src/notebooks/2.\ Testing\ Graph\ Patterns.ipynb
```

## Run Notebooks

### Requirements

```bash
pip install jupyter notebook
```

### Open Notebook

```bash
# From project root
jupyter notebook src/notebooks/
```

### Run All Cells

In Jupyter:
1. Menu: `Cell` → `Run All`
2. Or use `Shift + Enter` to run cell by cell

## References

- [Quickstart Guide](../guides/en-quickstart.md)
- [Full Documentation](../README.md)
