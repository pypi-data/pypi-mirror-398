# GraphRAG: Fundamentos Teóricos

## ¿Qué es GraphRAG?

GraphRAG (Graph Retrieval-Augmented Generation) es un enfoque avanzado de RAG que utiliza grafos de conocimiento para mejorar la recuperación y generación de información.

**Idea central**: Valerse de las relaciones entre la data a ser recuperada en el RAG. En lugar de buscar solo por similitud vectorial, GraphRAG aprovecha la estructura del grafo para enriquecer la búsqueda y recuperación.

## Conceptos Fundamentales

### RAG Tradicional vs GraphRAG

**RAG Tradicional:**
- Usa búsqueda vectorial simple
- No considera relaciones entre documentos
- Limitado a similitud semántica

**GraphRAG:**
- Usa estructura del grafo para enriquecer búsqueda
- Considera relaciones entre entidades
- Combina múltiples señales (texto, vectorial, estructura)

## Tipos de Grafos en GraphRAG

### Lexical Graphs (Grafos Léxicos)

Estructuras que organizan texto y capturan relaciones lingüísticas. Se enfocan en la estructura del lenguaje y facilitan la búsqueda semántica.

**Características**:
- Organizan texto en chunks relacionados
- Contienen embeddings para búsqueda semántica
- Relaciones estructurales (CONTAINS, HAS_CHUNK, NEXT_CHUNK)
- Compatibles con patrones básicos de GraphRAG

**En Ungraph**: El patrón `FILE_PAGE_CHUNK` es un Lexical Graph. Ver [Lexical Graphs](../concepts/sp-lexical-graphs.md) para más detalles.

### Knowledge Graphs (Grafos de Conocimiento)

Estructuras que representan conocimiento factual y relaciones entre entidades del dominio. Se enfocan en hechos verificables y esquemas estructurados.

**Características**:
- Representan entidades y relaciones del dominio
- Esquemas estructurados conocidos
- Relaciones semánticas (AUTOR_DE, PARTE_DE, etc.)
- Requieren estrategias especiales para recuperación (Templates de Cypher, Generación Dinámica)

## Patrones de Búsqueda GraphRAG

### 1. Basic Retriever (Recuperación Básica)

**También conocido como**: Recuperador Ingenuo, RAG Básico, RAG Típico

**Patrón de grafo requerido**: Lexical Graph

**Cómo funciona**:
- La pregunta del usuario se vectoriza usando el mismo modelo de embeddings que los chunks
- Se ejecuta búsqueda de similitud en los embeddings de los chunks
- Se recuperan los `k` chunks más similares

**Cuándo usar**: Cuando la información solicitada se encuentra en nodos específicos relacionados con temas distribuidos en uno o más chunks, pero no en un número elevado de ellos.

**No requiere consulta adicional**: La búsqueda de similitud se realiza directamente sobre los nodos.

**Referencia:** [GraphRAG Basic Retriever](https://graphrag.com/reference/graphrag/basic-retriever/)

### 2. Parent-Child Retriever

**También conocido como**: Recuperador Padre-Documento

**Patrón de grafo requerido**: Lexical Graph con estructura jerárquica

**Evolución del Lexical Graph**: Divide documentos grandes en partes más pequeñas (chunks) para crear embeddings más significativos. Se crea una jerarquía donde:
- **Chunks pequeños (hijos)**: Contienen texto embebido y embeddings (mejor representación vectorial)
- **Chunks grandes (padres)**: Solo se usan para contexto en generación de respuestas

**Relaciones**: `PART_OF`, `HAS_CHILD`

**Cómo funciona**:
- Busca en chunks pequeños (mejor matching vectorial, menos ruido)
- Recupera el chunk padre (contexto completo para generación)

**Cuándo usar**: Cuando muchos temas en un chunk afectan negativamente la calidad de los vectores, pero necesitas contexto completo para generar respuestas.

**Referencia:** [GraphRAG Parent-Child Retriever](https://graphrag.com/reference/graphrag/parent-child-retriever/)

### 3. Hypothetical Question Retriever

**Idea**: Generar preguntas hipotéticas para cada chunk usando un LLM para mejorar el matching entre preguntas del usuario y contenido disponible.

**Cómo funciona**:
- Se usa un LLM para generar preguntas y respuestas para cada chunk
- La búsqueda de similitud se efectúa en las preguntas generadas
- Se encuentran las preguntas más similares y se devuelven los chunks correspondientes

**Cuándo usar**: Cuando la similitud entre los vectores de la pregunta del usuario y los vectores de los chunks es baja. Este procedimiento incrementa la similitud entre el usuario y el texto disponible.

**Requisito**: Requiere más procesamiento por parte del LLM al precisar generar preguntas por chunk.

**Referencia:** [GraphRAG Hypothetical Question Retriever](https://graphrag.com/reference/graphrag/hypothetical-question-retriever/)

### 4. Community Summary Retriever

Encuentra comunidades de nodos relacionados y genera resúmenes.

**Referencia:** [GraphRAG Community Summary Retriever](https://graphrag.com/reference/graphrag/community-summary-retriever/)

### 5. Graph-Enhanced Vector Search

Combina búsqueda vectorial con estructura del grafo.

**Referencia:** [GraphRAG Graph-Enhanced Vector Search](https://graphrag.com/reference/graphrag/graph-enhanced-vector-search/)

### 6. Domain Graphs (Grafos de Dominio)

Grafos estructurados con esquemas conocidos. No podemos conocer de antemano qué estructura tendrán las entidades, muchas veces obedecen a una estructura proveniente de datos estructurados (como cuando se mapea de una base de datos relacional al grafo).

**Estrategias de recuperación**:
- **Templates de Cypher**: Conjunto de queries por defecto que pueden ser populados a partir de las preguntas de los usuarios. El LLM extrae parámetros y decide qué template usar.
- **Generación Dinámica de Cypher**: El LLM genera queries Cypher dinámicamente basado en la pregunta del usuario.

**Cuándo usar**: Cuando tienes datos estructurados con esquemas conocidos y necesitas recuperación determinista de datos estructurados.

## Investigación y Papers

### Papers Principales

1. **Retrieval-Augmented Generation with Graphs (GraphRAG)**
   - Microsoft Research
   - [Link](https://graphrag.com/appendices/research/)

2. **Graph Retrieval-Augmented Generation: A Survey**
   - Revisión completa del estado del arte
   - [Link](https://graphrag.com/appendices/research/)

### Conceptos Clave de los Papers

- **Knowledge Graphs**: Estructura de conocimiento explícita
- **Graph Traversal**: Navegación por relaciones del grafo
- **Community Detection**: Identificación de comunidades relacionadas
- **Hybrid Retrieval**: Combinación de múltiples señales

## Aplicaciones

### Casos de Uso

1. **Documentación Técnica**: Búsqueda semántica en documentación
2. **Investigación Académica**: Exploración de papers relacionados
3. **Knowledge Bases**: Bases de conocimiento empresariales
4. **Q&A Systems**: Sistemas de pregunta-respuesta mejorados

## Referencias

- [GraphRAG Documentation](https://graphrag.com/)
- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [GraphRAG Research Papers](https://graphrag.com/appendices/research/)
- [Neo4j GraphRAG Guide](https://go.neo4j.com/rs/710-RRC-335/images/Developers-Guide-GraphRAG.pdf)
