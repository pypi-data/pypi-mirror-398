# Notebooks de Ejemplo

Jupyter notebooks disponibles para aprender y probar Ungraph.

## Notebooks Disponibles

### 1. Using Ungraph Library

**Ubicación:** `src/notebooks/1. Using Ungraph Library.ipynb`

**Contenido:**
- Configuración de Neo4j
- Obtención de recomendaciones de chunking
- Ingesta de documentos (Markdown, TXT, Word, PDF)
- Búsqueda por texto
- Búsqueda híbrida
- Pipeline completo end-to-end

**Uso:**
```bash
jupyter notebook src/notebooks/1.\ Using\ Ungraph\ Library.ipynb
```

### 2. Testing Graph Patterns

**Ubicación:** `src/notebooks/2. Testing Graph Patterns.ipynb`

**Contenido:**
- Value Objects (NodeDefinition, RelationshipDefinition, GraphPattern)
- Patrones predefinidos (FILE_PAGE_CHUNK_PATTERN)
- PatternService (validación y generación de Cypher)
- Creación de patrones personalizados
- Tests sistemáticos de todas las funcionalidades

**Uso:**
```bash
jupyter notebook src/notebooks/2.\ Testing\ Graph\ Patterns.ipynb
```

## Ejecutar Notebooks

### Requisitos

```bash
pip install jupyter notebook
```

### Abrir Notebook

```bash
# Desde la raíz del proyecto
jupyter notebook src/notebooks/
```

### Ejecutar Todas las Celdas

En Jupyter:
1. Menú: `Cell` → `Run All`
2. O usar `Shift + Enter` para ejecutar celda por celda

## Referencias

- [Guía de Inicio Rápido](../guides/sp-quickstart.md)
- [Documentación Completa](../README.md)
