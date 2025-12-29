# Plan de Publicación - Ungraph v0.1.0 (Release Completo ETI)

**Objetivo**: Preparar primera versión publicable del artículo con implementación completa del patrón ETI (Extract-Transform-Inference).

**Principio**: Implementar fase de inferencia mínima viable y organizar diseño experimental con matriz de componentes disponibles.

**Estado**: Este documento es el **faro principal** para todas las acciones del release v0.1.0. Toda la información relevante está consolidada aquí.

**Estado Actual del Release v0.1.0**: ✅ **IMPLEMENTACIÓN Y DOCUMENTACIÓN COMPLETAS** - Solo falta validación final.

---

## 🚀 Guía Rápida: Publicación en TestPyPI

**Pasos esenciales para publicar en TestPyPI:**

1. **Preparar credenciales:**
   - Crear cuenta en https://test.pypi.org/account/register/
   - Generar API token en https://test.pypi.org/manage/account/#api-tokens
   - Configurar token: `export UV_PUBLISH_TOKEN="pypi-xxxxxxxxxxxxx"`

2. **Build del paquete:**
   ```bash
   uv build
   ```

3. **Publicar en TestPyPI:**
   ```bash
   uv publish --publish-url https://test.pypi.org/legacy/ --token $UV_PUBLISH_TOKEN dist/*
   ```

4. **Verificar instalación desde TestPyPI:**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ungraph==0.1.0
   ```

**Nota:** Ver sección completa "Validaciones para PyPI Build" (línea 647) para checklist detallado.

---

## 📊 Análisis: Código vs Documentación

### ✅ Lo que SÍ está implementado

1. **Extract (E)**: ✅
   - `LangChainDocumentLoaderService` - carga documentos
   - Soporte Markdown, TXT, Word
   - Detección de encoding

2. **Transform (T)**: ✅
   - `ChunkingService` - múltiples estrategias
   - `EmbeddingService` - HuggingFace embeddings
   - Persistencia en Neo4j (File → Page → Chunk)

3. **Búsqueda GraphRAG básica**: ✅
   - Basic Retriever
   - Parent-Child Retriever
   - Hybrid Search
   - Metadata Filtering

4. **Arquitectura**: ✅
   - Clean Architecture implementada
   - Tests funcionando
   - API pública (`ungraph.ingest_document()`, `ungraph.search()`)

### ✅ Lo que YA está implementado (Release Completo)

1. **Inference (I) explícita**: ✅ COMPLETO
   - ✅ Servicio de inferencia (interfaz + implementación `SpacyInferenceService`)
   - ✅ Extracción de facts/relations estructurada
   - ✅ Generación de facts simples (MENTIONS) y relaciones de co-ocurrencia
   - ✅ Persistencia de facts en Neo4j

2. **PROV-O integrado**: ✅ COMPLETO (básico)
   - ✅ Trazabilidad básica (wasDerivedFrom) implementada
   - ✅ Integración con código principal
   - ✅ Trazabilidad end-to-end automática (Fact → Chunk → Document)

3. **Experimentos reales**: 🟢 BAJO (puede ser planificado)
   - ⚠️ Solo demos con datos mock
   - ❌ No hay datasets reales (EDGAR, BioASQ, etc.)
   - ❌ No hay métricas calculadas
   - **Para release**: Diseño experimental completo con matriz de componentes

4. **Ontología formal**: 🟢 BAJO
   - ❌ No existe `docs/ontology.md` formal
   - ❌ No existe `docs/ontology.owl`
   - ⚠️ Solo estructura implícita en código
   - **Para release**: Documentación mínima de ontología File/Page/Chunk

---

## 🎯 Estrategia: Implementación Mínima Viable de ETI

### Objetivo del Release

**Implementar fase de Inferencia mínima viable** que permita:
1. Extracción de entidades y relaciones básicas desde chunks
2. Generación de tripletas (subject-predicate-object) con confianza
3. Persistencia de facts en Neo4j como nodos/relaciones
4. Trazabilidad básica con PROV-O (wasDerivedFrom)

### Componentes Disponibles para Matriz Experimental

**Fase Extract (E)**: ✅ Completo
- `LangChainDocumentLoaderService` - Markdown, TXT, Word
- Detección de encoding automática

**Fase Transform (T)**: ✅ Completo
- **Chunking**: 
  - RecursiveCharacter (default)
  - Smart chunking: Fixed, Lexical, Semantic, Hierarchical
  - Estrategias: Character, Recursive, Token, MarkdownHeader, HTMLHeader, PythonCode, Semantic, LanguageSpecific
- **Embeddings**: 
  - HuggingFace (all-MiniLM-L6-v2 por defecto, configurable)
  - Dimensiones: 384 (default), otros modelos configurables
- **Persistencia**: Neo4j con patrón FILE_PAGE_CHUNK

**Fase Inference (I)**: ✅ COMPLETO
- ✅ Interfaz `InferenceService` en `domain/services/`
- ✅ Implementación básica `SpacyInferenceService` en `infrastructure/services/`
- ✅ Implementación única: NER-only (spaCy) para v0.1.0
- ⚠️ Opciones futuras: LM-only (LLM), Hybrid (v0.2.0+)

**Retrieval Patterns**: ✅ Disponibles
- Basic Retriever
- Parent-Child Retriever
- Hybrid Search (text + vector)
- Metadata Filtering
- Graph-Enhanced Vector Search (requiere GDS)
- Local Retriever (requiere GDS)
- Community Summary Retriever (requiere GDS)

---

## 📊 Matriz de Experimentación: Espacio de Componentes

### Componentes Disponibles para Combinar

| Componente | Tipo | Opciones Disponibles | Estado |
|------------|------|---------------------|--------|
| **Chunking** | Estrategia | `recursive`, `character`, `token`, `markdown_header`, `html_header`, `python_code`, `semantic`, `language_specific` | ✅ |
| **Chunking Smart** | Modo | `fixed`, `lexical`, `semantic`, `hierarchical` | ✅ |
| **Embedding Model** | Modelo | `all-MiniLM-L6-v2` (default), otros HuggingFace | ✅ |
| **Retrieval Pattern** | Patrón | `basic`, `parent_child`, `hybrid`, `metadata_filtering`, `graph_enhanced_vector`, `local`, `community_summary` | ✅ |
| **Inference Type** | Tipo | `ner-only` (spaCy) | ✅ Implementado (v0.1.0) |
| **Domain** | Dominio | `finance`, `biomedical`, `scientific`, `general` | ⚠️ Planificado |

### Matriz de Experimentación (Espacio de Búsqueda)

**Dimensiones del espacio experimental:**

```
Experimento = f(Chunking, Embedding, Retrieval, Inference, Domain)
```

**Combinaciones prioritarias para Release v0.1.0:**

| ID | Chunking | Embedding | Retrieval | Inference | Domain | Prioridad |
|----|----------|-----------|-----------|-----------|--------|-----------|
| E1 | `recursive` | `all-MiniLM-L6-v2` | `basic` | `ner-only` | `finance` | 🔴 Alta |
| E2 | `recursive` | `all-MiniLM-L6-v2` | `parent_child` | `ner-only` | `finance` | 🔴 Alta |
| E3 | `semantic` | `all-MiniLM-L6-v2` | `hybrid` | `ner-only` | `biomedical` | 🟡 Media |
| E4 | `lexical` | `all-MiniLM-L6-v2` | `graph_enhanced_vector` | `ner-only` | `scientific` | 🟡 Media |
| E5 | `hierarchical` | `all-MiniLM-L6-v2` | `community_summary` | `ner-only` | `general` | 🟢 Baja |

**Nota**: Para release v0.1.0, solo se implementa `ner-only` (spaCy). 
Implementaciones LLM (`lm-only`, `hybrid`) están documentadas como alternativas 
futuras (ver referencia a Neo4j LLM Graph Builder en código).

**Ablation Studies (Control vs ETI):**

| Baseline | Variante | Diferencia | Objetivo |
|----------|----------|------------|----------|
| ET (sin I) | ETI (con I) | Fase Inference | Medir impacto de inferencia |
| `basic` retrieval | `parent_child` | Patrón retrieval | Medir impacto de contexto |
| `recursive` chunking | `semantic` chunking | Estrategia chunking | Medir impacto de chunking |

**Nota**: Estudios de ablación con diferentes tipos de inferencia (`lm-only`, `hybrid`) 
quedan para futuras versiones. Release v0.1.0 implementa solo `ner-only` (spaCy).

### Diseño Experimental: Matriz de Factores

**Factores principales (variables independientes):**
1. **Chunking Strategy**: {recursive, semantic, lexical, hierarchical}
2. **Retrieval Pattern**: {basic, parent_child, hybrid, graph_enhanced}
3. **Inference Type**: {none, ner-only} (v0.1.0 implementa solo ner-only con spaCy)
4. **Domain**: {finance, biomedical, scientific, general}

**Variables dependientes (métricas):**
- **Retrieval**: recall@k, MRR, precision@k
- **QA**: F1-score (micro/macro), exact match
- **Inference**: precision, recall, F1 sobre facts extraídos
- **Hallucination**: tasa de facts no groundeados
- **Performance**: latencia (ms), throughput (docs/sec)

**Hipótesis experimentales:**
- **H1**: ETI (con Inference) > ET (sin Inference) en recall@k y QA-F1
- **H2**: Semantic chunking > Recursive chunking para dominios técnicos
- **H3**: Parent-Child retrieval > Basic retrieval para preguntas que requieren contexto
- **H4**: [Futuro] Hybrid inference > LM-only para precisión de facts extraídos

---

## 📋 Tareas Críticas: Implementación + Documentación

### 🔴 PRIORIDAD 0: Implementar Fase de Inferencia con spaCy (6-8 horas)

**Objetivo**: Crear servicio de inferencia mínima viable usando spaCy, siguiendo Clean Architecture estricta.

**Alcance del Release (Closure)**: ✅ COMPLETO
- ✅ Implementación única con spaCy (NER-only)
- ✅ Extracción de entidades básicas (PERSON, ORG, LOC, etc.)
- ✅ Generación de facts simples (MENTIONS)
- ✅ Persistencia en Neo4j
- ✅ Trazabilidad básica PROV-O
- ✅ LLM como alternativa futura (documentado en código, no implementado)

#### Arquitectura: Patrón Clean Architecture

**Estructura siguiendo el patrón existente:**

```
domain/
  ├── services/
  │   └── inference_service.py          # Interfaz (ABC)
  ├── entities/
  │   ├── fact.py                       # Entidad Fact
  │   ├── entity.py                      # Entidad Entity
  │   └── relation.py                   # Entidad Relation
  └── value_objects/
      └── provenance.py                 # Value Object

application/
  └── use_cases/
      └── ingest_document.py            # Modificar: añadir fase Inference

infrastructure/
  ├── services/
  │   └── spacy_inference_service.py    # Implementación con spaCy
  └── repositories/
      └── neo4j_chunk_repository.py    # Modificar: añadir save_facts()
```

#### Componentes a Implementar

1. **Interfaz de dominio** (`InferenceService`):
   ```python
   # src/domain/services/inference_service.py
   class InferenceService(ABC):
       """
       Interfaz para servicios de inferencia.
       
       Esta interfaz define las operaciones para extraer entidades, relaciones
       y facts desde chunks de texto.
       
       Nota sobre implementaciones alternativas:
       - La extracción de entidades puede realizarse también usando LLMs
         (OpenAI, Claude, Gemini, etc.) para obtener mayor flexibilidad y
         capacidad de extraer relaciones complejas. Para referencia, ver
         el trabajo de Neo4j con LLM Graph Builder:
         https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/
       
       La implementación actual usa spaCy (NER-only) como solución mínima
       viable para el release v0.1.0. Implementaciones LLM pueden añadirse
       en futuras versiones siguiendo el mismo patrón de arquitectura.
       """
       
       @abstractmethod
       def extract_entities(self, chunk: Chunk) -> List[Entity]:
           """Extrae entidades nombradas del chunk"""
           pass
       
       @abstractmethod
       def extract_relations(self, chunk: Chunk) -> List[Relation]:
           """Extrae relaciones entre entidades"""
           pass
       
       @abstractmethod
       def infer_facts(self, chunk: Chunk) -> List[Fact]:
           """
           Genera facts estructurados (subject-predicate-object).
           
           Returns:
               Lista de facts con subject, predicate, object, confidence y provenance
           """
           pass
   ```

2. **Entidades de dominio**:
   - `Fact`: subject, predicate, object, confidence (0.0-1.0), provenance_ref
   - `Entity`: name, type (PERSON, ORGANIZATION, LOCATION, etc.), mentions
   - `Relation`: source_entity, target_entity, relation_type, confidence

3. **Implementación con spaCy** (ÚNICA para release):
   ```python
   # src/infrastructure/services/spacy_inference_service.py
   class SpacyInferenceService(InferenceService):
       """
       Implementación de InferenceService usando spaCy para NER.
       
       Esta es la implementación de referencia para el release v0.1.0.
       Usa spaCy para extracción de entidades nombradas (NER) y genera
       facts simples del tipo (chunk_id, "MENTIONS", entity_name).
       
       Nota: Para extracción más avanzada con LLMs, ver documentación
       de InferenceService y referencia a Neo4j LLM Graph Builder.
       """
   ```

4. **Caso de uso actualizado**:
   ```python
   # src/application/use_cases/ingest_document.py
   class IngestDocumentUseCase:
       def __init__(
           self,
           ...,
           inference_service: Optional[InferenceService] = None  # Nueva dependencia
       ):
           ...
       
       def execute(...):
           # 1. Extract
           document = self.document_loader_service.load(...)
           # 2. Transform
           chunks = self.chunking_service.chunk(...)
           embeddings = self.embedding_service.generate_embeddings_batch(...)
           # 3. Inference (NUEVO)
           if self.inference_service:
               facts = []
               for chunk in chunks:
                   chunk_facts = self.inference_service.infer_facts(chunk)
                   facts.extend(chunk_facts)
               # Persistir facts
               self.chunk_repository.save_facts(facts)
   ```

5. **Persistencia en Neo4j**:
   - Crear nodos `Fact` con propiedades: subject, predicate, object, confidence
   - Crear relaciones `DERIVED_FROM` entre Fact y Chunk (provenance)
   - Crear nodos `Entity` y relaciones `MENTIONS` entre Chunk y Entity

#### Tareas Detalladas (Seguir Clean Architecture)

1. **Crear interfaz en domain** (1.5 horas):
   - `src/domain/services/inference_service.py`
   - Métodos: `extract_entities()`, `extract_relations()`, `infer_facts()`
   - **Documentar**: LLM como alternativa futura, referencia a Neo4j LLM Graph Builder
   - Retornar entidades `Fact`, `Entity`, `Relation`

2. **Crear entidades de dominio** (1 hora):
   - `src/domain/entities/fact.py` - Fact con subject, predicate, object, confidence, provenance
   - `src/domain/entities/entity.py` - Entity con name, type, mentions
   - `src/domain/entities/relation.py` - Relation entre entidades
   - `src/domain/value_objects/provenance.py` - Provenance info (wasDerivedFrom, timestamp)

3. **Implementar servicio spaCy** (3-4 horas):
   - `src/infrastructure/services/spacy_inference_service.py`
   - Usar spaCy para NER (modelo `en_core_web_sm` o similar)
   - Extraer entidades: PERSON, ORG, LOC, GPE, etc.
   - Generar facts: (chunk_id, "MENTIONS", entity_name)
   - Generar relaciones simples entre entidades co-ocurrentes
   - **Documentar en código**: LLM como alternativa futura

4. **Modificar caso de uso** (1 hora):
   - `src/application/use_cases/ingest_document.py`
   - Añadir `inference_service` como dependencia opcional
   - Llamar a `inference_service.infer_facts()` después de chunking
   - Orquestar persistencia de facts

5. **Modificar repository** (1 hora):
   - `src/infrastructure/repositories/neo4j_chunk_repository.py`
   - Añadir método `save_facts(facts: List[Fact])`
   - Crear nodos Fact y Entity en Neo4j
   - Crear relaciones DERIVED_FROM y MENTIONS

6. **Actualizar dependencies.py** (0.5 horas):
   - `src/application/dependencies.py`
   - Crear factory para `SpacyInferenceService`
   - Inyectar en `IngestDocumentUseCase`

7. **Tests** (1 hora):
   - Tests unitarios de `SpacyInferenceService`
   - Tests de integración con pipeline completo
   - Validar que facts se persisten correctamente

**Archivos a crear/modificar**:
- `src/domain/services/inference_service.py` (nuevo) - Interfaz con documentación LLM
- `src/domain/entities/fact.py` (nuevo)
- `src/domain/entities/entity.py` (nuevo)
- `src/domain/entities/relation.py` (nuevo)
- `src/infrastructure/services/spacy_inference_service.py` (nuevo) - Implementación única
- `src/application/use_cases/ingest_document.py` (modificar)
- `src/infrastructure/repositories/neo4j_chunk_repository.py` (modificar: añadir `save_facts()`)
- `src/application/dependencies.py` (modificar: factory para inference service)

---

### 🔴 PRIORIDAD 1: Corregir Referencias (2 horas)

**Problema**: Referencias duplicadas, faltantes, formato inconsistente.

**Acciones**:
1. Corregir línea 104 de `article/ungraph.md`:
   - Cambiar `[2]` duplicado → `[3]` para Neo4j GraphRAG
2. Añadir a `article/references.bib`:
   ```bibtex
   @misc{neo4j2024graphrag,
     title={GraphRAG Patterns Catalog},
     author={{Neo4j, Inc.}},
     year={2024},
     howpublished={\url{https://graphrag.com/reference/}},
     note={Accessed: 2025-12-25}
   }
   ```
3. Renumerar referencias posteriores
4. Completar DOIs faltantes (buscar en Google Scholar)
5. Estandarizar formato: numérico `[1]`, `[2]` en todo el documento

**Archivos**:
- `article/ungraph.md` (líneas 102-106, 137-142)
- `article/references.bib`

---

### 🔴 PRIORIDAD 2: Reescribir Abstract (1 hora)

**Problema**: Abstract actual es muy breve y no sigue estructura IMRAD.

**Nuevo abstract** (150-200 palabras):
```
Las arquitecturas modernas de Retrieval-Augmented Generation (RAG) enfrentan 
desafíos en la construcción de grafos de conocimiento confiables y trazables. 
Este trabajo propone el patrón Extract-Transform-Inference (ETI) como evolución 
del tradicional ETL, añadiendo una fase explícita de inferencia que genera hechos 
normalizados con trazabilidad PROV-O. 

Presentamos una implementación parcial de ETI en la librería Ungraph, que 
construye Lexical Graphs sobre Neo4j integrando chunking estratégico, embeddings 
vectoriales y patrones GraphRAG básicos. La implementación actual cubre las fases 
Extract y Transform; la fase Inference se propone conceptualmente y se valida 
mediante demos con datos mock.

[Para versión completa:] Evaluamos la efectividad mediante experimentos reproducibles 
en cuatro dominios (financiero, biomédico, científico y general), comparando pipelines 
control (ET) versus ETI en métricas de recuperación (recall@k, MRR), calidad de QA 
(F1), precisión de inferencia y tasa de hallucination. [Resultados pendientes de 
ejecución experimental].

El patrón ETI proporciona un marco coherente para construir sistemas de conocimiento 
confiables, integrando principios de ingeniería del conocimiento, Web semántica 
(ontologías, PROV) y neuro-symbolic computing.
```

**Archivo**: `article/ungraph.md` (líneas 3-4)

---

### 🟡 PRIORIDAD 3: Documentar Matriz de Experimentación (2 horas)

**Objetivo**: Añadir sección de diseño experimental con matriz de componentes al artículo.

**Acciones**:
1. Añadir sección "Diseño Experimental" después de "Metodología experimental":
   ```markdown
   ## Diseño Experimental: Matriz de Componentes
   
   Para evaluar el patrón ETI, diseñamos un espacio experimental multidimensional 
   que combina diferentes componentes disponibles en Ungraph:
   
   ### Componentes del Espacio Experimental
   
   - **Chunking**: {recursive, semantic, lexical, hierarchical}
   - **Embedding**: {all-MiniLM-L6-v2, otros modelos HuggingFace}
   - **Retrieval**: {basic, parent_child, hybrid, graph_enhanced_vector}
   - **Inference**: {none, lm-only, ner-only, hybrid}
   - **Domain**: {finance, biomedical, scientific, general}
   
   ### Matriz de Experimentos Prioritarios
   
   [Tabla con combinaciones E1-E5 de la matriz anterior]
   
   ### Ablation Studies
   
   [Tabla con estudios de ablación: ET vs ETI, chunking strategies, etc.]
   ```

2. Actualizar sección "Metodología experimental" con referencia a matriz

**Archivo**: `article/ungraph.md`

---

### 🟡 PRIORIDAD 4: Añadir Research Questions (1 hora)

**Problema**: No hay RQs explícitas (requerido para paper científico).

**Acciones**:
1. Añadir sección antes de "Metodología experimental":
   ```markdown
   ## Research Questions e Hipótesis
   
   ### Research Questions
   
   **RQ1: Efectividad de la Fase de Inferencia**
   ¿Añadir una fase explícita de inferencia (I) mejora la calidad de recuperación y 
   respuesta de preguntas comparado con pipelines que solo realizan extracción y 
   transformación (ET)?
   
   **RQ2: Tipos de Inferencia por Dominio**
   ¿Qué tipo de inferencia (LM-only, symbolic-only, neuro-symbolic) es más efectiva 
   para diferentes dominios de conocimiento (financiero, biomédico, científico, general)?
   
   **RQ3: Trade-off Trazabilidad vs Performance**
   ¿La trazabilidad completa con PROV-O mejora la confianza y explicabilidad del sistema 
   sin sacrificar significativamente el rendimiento (latencia, throughput)?
   
   **Nota**: Estas research questions guiarán los experimentos futuros una vez completada 
   la implementación de la fase Inference.
   ```

**Archivo**: `article/ungraph.md` (nueva sección)

---

### 🟡 PRIORIDAD 5: Formalizar Patrón ETI (2 horas)

**Problema**: Falta definición matemática formal.

**Acciones**:
1. Añadir después de línea 111:
   ```markdown
   ### Definición Formal del Patrón ETI
   
   **Definición 1 (Pipeline ETI):**
   Un pipeline ETI es una tupla P = (E, T, I, O, M) donde:
   
   - **E (Extractors)**: Conjunto de extractores {e₁, e₂, ..., eₙ} donde cada 
     eᵢ: Sources → Documents produce documentos estructurados con metadatos.
   
   - **T (Transformers)**: Conjunto de transformadores {t₁, t₂, ..., tₘ} donde cada 
     tⱼ: Documents → Chunks produce chunks con embeddings y anotaciones semánticas.
   
   - **I (Inference)**: Conjunto de modelos de inferencia {i₁, i₂, ..., iₖ} donde cada 
     iₖ: Chunks → (Facts ∪ Relations ∪ Explanations) genera artefactos de conocimiento 
     con señales de confianza y trazabilidad.
   
   - **O (Ontology)**: Esquema formal que define tipos de entidades, relaciones permitidas, 
     constraints y mapeos a vocabularios estándar (schema.org, PROV-O).
   
   - **M (Metadata)**: Estructura PROV-O que registra provenance de cada artefacto, 
     incluyendo: entidades derivadas, actividades ejecutadas, agentes responsables y timestamps.
   
   **Propiedades del Pipeline ETI:**
   1. **Trazabilidad**: Todo fact f ∈ Facts tiene prov:wasDerivedFrom apuntando a su chunk fuente
   2. **Validabilidad**: Todo fact f puede ser verificado contra source s mediante provenance chain
   3. **Composabilidad**: Pipelines ETI pueden encadenarse (salida de Iₖ → entrada de Eᵢ₊₁)
   4. **Reproducibilidad**: Dado mismo input + config + seed → mismo output
   ```

2. Añadir tabla comparativa ETL vs ETI (simple, en markdown)

**Archivo**: `article/ungraph.md`

---

## 🟢 Tareas Opcionales (Solo si hay tiempo)

### Opcional 1: Consolidar Documentación en `docs/` (1-2 horas)
**Objetivo**: Eliminar redundancias y consolidar documentación

**Archivos a consolidar/eliminar**:
- `docs/theory/GRAPHRAG_AVANZADO.md` → Consolidar contenido relevante en `docs/theory/graphrag.md` o eliminar si es solo guía futura
- `docs/validation/` → Consolidar múltiples archivos en uno solo (`validation_summary.md` + `README.md` son suficientes)
- `docs/examples/` → Revisar y consolidar ejemplos duplicados

**Criterio**: Mantener solo documentación que aporta valor único. Eliminar guías futuras o contenido duplicado.

### Opcional 2: Crear Tabla de Datasets (30 min)
- Crear `article/experiments/datasets.csv` con placeholders
- Mencionar que son datasets planificados

### Opcional 3: Añadir Diagrama ASCII (30 min)
- Diagrama simple de arquitectura ETI (ASCII art)
- Mostrar flujo Extract → Transform → Inference

### Opcional 4: Documentar Ontología Básica (1 hora)
- Crear `docs/ontology.md` mínimo
- Describir File/Page/Chunk/Fact (ya está en código)
- NO crear OWL completo (no necesario para v0.1.0)

---

## ✅ Lo que SÍ hacer para Release

1. ✅ **Implementar fase Inference mínima viable** - requerido para release completo
2. ✅ **Integrar PROV-O básico** - trazabilidad mínima (wasDerivedFrom)
3. ✅ **Diseñar matriz experimental** - documentar espacio de experimentación
4. ✅ **Crear servicios de inferencia** - siguiendo Clean Architecture
5. ✅ **Documentar ontología básica** - File/Page/Chunk/Fact

## ❌ Lo que NO hacer (fuera de scope v0.1.0)

1. ❌ **NO crear PROV-O completo** - solo integración básica
2. ❌ **NO ejecutar experimentos completos** - solo diseño y demos
3. ❌ **NO crear OWL completo** - solo documentación básica
4. ❌ **NO implementar razonamiento simbólico avanzado** - solo extracción básica

---

## 📅 Timeline Estimado

**Total: 10-12 horas de trabajo** (reducido al enfocarse solo en spaCy)

### Fase 1: Implementación (6-8 horas)
- Día 1 (1.5h): Prioridad 0 - Interfaz domain con documentación LLM
- Día 1 (1h): Prioridad 0 - Entidades domain
- Día 1-2 (3-4h): Prioridad 0 - Implementación spaCy
- Día 2 (1h): Prioridad 0 - Modificar caso de uso
- Día 2 (1h): Prioridad 0 - Modificar repository
- Día 2 (0.5h): Prioridad 0 - Actualizar dependencies.py
- Día 2 (1h): Prioridad 0 - Tests

### Fase 2: Documentación (6-8 horas)
- Día 3 (2h): Prioridad 1 (Referencias)
- Día 3 (1h): Prioridad 2 (Abstract)
- Día 4 (2h): Prioridad 3 (Matriz experimental)
- Día 4 (1h): Prioridad 4 (Research Questions)
- Día 5 (2h): Prioridad 5 (Formalización ETI)

### Fase 3: Validación (2-4 horas)
- Día 5-6 (2-4h): Tests end-to-end, demos, validación

---

## ✅ Checklist Final - Release v0.1.0

Antes de considerar "publicable":

### Implementación (Prioridad 0) - ✅ COMPLETO
- [x] Interfaz `InferenceService` creada en domain (con documentación LLM como futuro)
- [x] Entidades `Fact`, `Entity`, `Relation` creadas
- [x] Implementación `SpacyInferenceService` (única para v0.1.0)
- [x] Integración con `IngestDocumentUseCase`
- [x] Método `save_facts()` en repository
- [x] Factory en `dependencies.py`
- [x] Persistencia de facts en Neo4j
- [x] Trazabilidad PROV-O básica (wasDerivedFrom)
- [x] Tests unitarios e integración
- [x] Código sigue Clean Architecture estricta

### Documentación (Prioridades 1-5) - ✅ COMPLETO
- [x] Referencias corregidas y validadas (Prioridad 1)
  - Corregido [2] duplicado → [3] para Neo4j GraphRAG
  - Añadida entrada en `references.bib`
  - Referencias renumeradas correctamente (1-11)
- [x] Abstract reescrito (150-200 palabras, IMRAD) (Prioridad 2)
- [x] Sección "Matriz de Experimentación" añadida (Prioridad 3)
- [x] Research Questions explícitas (Prioridad 4)
  - RQ1: Efectividad de la Fase de Inferencia
  - RQ2: Tipos de Inferencia por Dominio
  - RQ3: Trade-off Trazabilidad vs Performance
- [x] Definición formal de ETI añadida (Prioridad 5)
- [x] Tabla comparativa ETL vs ETI (Prioridad 5)
- [x] Documento `article/ungraph.md` revisado para consistencia

### Validación - ⏳ PENDIENTE

#### Validaciones Funcionales
- [ ] Pipeline ETI completo funciona end-to-end (verificar con datos reales)
- [ ] Facts se persisten correctamente en Neo4j (verificar con datos reales)
- [ ] Tests pasan sin errores (verificar configuración pytest)
- [ ] Documentación revisada y sin contradicciones

#### Validaciones para PyPI Build

**1. Tests y Calidad de Código**
- [x] ✅ Corregido `pytest.ini` (removidas opciones de timeout problemáticas)
- [x] ✅ Tests básicos funcionan: `pytest tests/test_inference_service.py::TestFactEntity::test_fact_creation -v` (PASSED)
- [x] ✅ Imports básicos funcionan: `from domain.entities.fact import Fact` (OK)
- [x] ⚠️ Script de integración ejecutado: `python scripts/test_eti_integration.py` (2/3 pruebas pasadas, falta spaCy)
- [ ] Ejecutar todos los tests unitarios: `pytest tests/ -m unit -v` (requiere instalar dependencias)
- [ ] Verificar que las dependencias opcionales funcionan (`ungraph[infer]`, `ungraph[gds]`)

**2. Build del Paquete**
- [ ] Verificar `pyproject.toml` tiene versión correcta (0.1.0)
- [ ] Verificar que todos los paquetes en `src/` están incluidos en `[tool.hatch.build.targets.wheel]`
- [ ] Build local: `uv build` (genera dist/ungraph-0.1.0.tar.gz y .whl)
- [ ] Verificar que el build no tiene errores ni warnings
- [ ] Verificar que el archivo .whl contiene todos los módulos necesarios (usar `scripts/verify_wheel.py`)

**3. Instalación y Verificación**
- [ ] Instalación limpia desde wheel: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl`
- [ ] Verificar que `ungraph` se puede importar: `python -c "import ungraph"`
- [ ] Verificar que las entidades se pueden importar: `from ungraph.domain.entities import Fact, Entity, Relation`
- [ ] Verificar que los servicios se pueden importar: `from ungraph.domain.services import InferenceService`
- [ ] Verificar que el caso de uso funciona: `from ungraph.application.use_cases import IngestDocumentUseCase`
- [ ] Verificar instalación con extras: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl[infer]`
- [ ] Ejecutar script de verificación: `python scripts/verify_installation.py`

**4. Tests Post-Instalación**
- [ ] Crear entorno virtual limpio: `python -m venv test_env`
- [ ] Activar entorno: `test_env\Scripts\activate` (Windows) o `source test_env/bin/activate` (Linux/Mac)
- [ ] Instalar desde wheel: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl`
- [ ] Ejecutar tests básicos en entorno limpio: `pytest tests/ -m unit -v`
- [ ] Verificar que las dependencias opcionales se instalan correctamente: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl[infer]`

**5. TestPyPI (Recomendado antes de PyPI oficial)**

**Preparación:**
- [x] ✅ Crear cuenta en TestPyPI: https://test.pypi.org/account/register/
- [x] ✅ Generar API token en TestPyPI: https://test.pypi.org/manage/account/#api-tokens
- [ ] Configurar credenciales (opción 1 - archivo `~/.pypirc`):
  ```ini
  [distutils]
  index-servers = testpypi

  [testpypi]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = pypi-xxxxxxxxxxxxx  # Token de TestPyPI
  ```
- [ ] O configurar variable de entorno (opción 2):
  ```bash
  export UV_PUBLISH_TOKEN="pypi-xxxxxxxxxxxxx"  # Token de TestPyPI
  export UV_PUBLISH_URL="https://test.pypi.org/legacy/"
  ```

**Publicación:**
- [x] ✅ Build del paquete: `uv build` (completado)
- [x] ✅ Verificar archivos generados en `dist/`: `ungraphx-0.1.0-py3-none-any.whl` y `ungraphx-0.1.0.tar.gz`
- [x] ✅ Subir a TestPyPI usando `uv`:
  ```bash
  uv publish --publish-url https://test.pypi.org/legacy/ --token $env:UV_PUBLISH_TOKEN dist/ungraphx-*
  ```
  **Nota:** Se publicó como `ungraphx` porque `ungraph` ya existe en TestPyPI (pertenece a otro usuario)
- [x] ✅ Verificar publicación en: https://test.pypi.org/project/ungraphx/

**Verificación Post-Publicación:**
- [ ] Crear entorno virtual limpio para prueba:
  ```bash
  python -m venv test_env
  test_env\Scripts\activate  # Windows
  # source test_env/bin/activate  # Linux/Mac
  ```
- [ ] Instalar desde TestPyPI (usar nombre temporal `ungraphx`):
  ```bash
  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ungraphx==0.1.0
  ```
  (Nota: `--extra-index-url` necesario porque TestPyPI no tiene todas las dependencias)
- [ ] Verificar instalación: `python -c "import ungraphx; print(ungraphx.__version__)"`
- [ ] Verificar imports críticos: `python scripts/verify_installation.py`
- [ ] Verificar que README.md se renderiza correctamente en TestPyPI

**6. PyPI Oficial (Después de validar TestPyPI)**

**Preparación:**
- [x] ✅ Verificar que `ungraph` NO existe en PyPI oficial (verificado: ✅ DISPONIBLE)
- [ ] Crear cuenta en PyPI oficial: https://pypi.org/account/register/ (si no existe)
- [ ] Generar API token en PyPI oficial: https://pypi.org/manage/account/#api-tokens
- [ ] Configurar token: `$env:UV_PUBLISH_TOKEN="pypi-token-pypi-oficial"`

**Publicación en PyPI Oficial:**
- [ ] Verificar que `pyproject.toml` tiene `name = "ungraph"` (nombre original restaurado)
- [ ] Build del paquete: `uv build`
- [ ] Verificar archivos generados: `ungraph-0.1.0-py3-none-any.whl` y `ungraph-0.1.0.tar.gz`
- [ ] Publicar en PyPI oficial:
  ```bash
  uv publish --token $env:UV_PUBLISH_TOKEN dist/ungraph-*
  ```
  (Sin `--publish-url` para usar PyPI oficial por defecto)
- [ ] Verificar publicación en: https://pypi.org/project/ungraph/
- [ ] Instalar desde PyPI oficial: `pip install ungraph==0.1.0`
- [ ] Verificar instalación y funcionalidad completa

**6. Documentación del Paquete**
- [ ] Verificar que README.md está completo y actualizado
- [ ] Verificar que LICENSE está presente
- [ ] Verificar que CHANGELOG.md existe (opcional pero recomendado)
- [ ] Verificar que las dependencias están correctamente especificadas
- [ ] Verificar que los extras opcionales están documentados

**7. Validación Final Pre-Release**
- [ ] Verificar que la versión en `pyproject.toml` coincide con el release
- [ ] Verificar que no hay archivos temporales o de desarrollo en el build
- [ ] Verificar que los notebooks no se incluyen en el paquete (correcto según pyproject.toml)
- [ ] Instalar dependencias de desarrollo: `uv pip install -e ".[dev]"`
- [ ] Ejecutar linting: `ruff check src/` (Ruff está en dependencias dev, línea 77 de pyproject.toml)
- [ ] Verificar que no hay secrets o información sensible en el código

---

## 🎯 Resultado Esperado: Closure del Release v0.1.0

**Release v0.1.0 completo que incluye**:

### Implementación
1. ✅ Pipeline ETI completo (Extract + Transform + Inference)
2. ✅ `SpacyInferenceService` implementado (NER básico, única implementación)
3. ✅ Persistencia de facts en Neo4j
4. ✅ Trazabilidad básica PROV-O (wasDerivedFrom)
5. ✅ Código siguiendo Clean Architecture estricta

### Documentación Científica
6. ✅ Abstract profesional (150-200 palabras, IMRAD)
7. ✅ Research Questions explícitas
8. ✅ Definición formal de ETI
9. ✅ Matriz de experimentación documentada
10. ✅ Diseño experimental con espacio de componentes
11. ✅ Hipótesis experimentales formuladas
12. ✅ Referencias correctas y completas

### Valor Entregado
- ✅ Librería funcional con ETI completo
- ✅ Implementación mínima viable con spaCy
- ✅ Base para experimentación futura
- ✅ Documentación científica rigurosa
- ✅ Diseño experimental reproducible
- ✅ Arquitectura extensible (LLM puede añadirse en v0.2.0+)

**Alcance del Release v0.1.0 (Closure)**:
- ✅ **Incluye**: spaCy NER-only como única implementación de Inference
- ✅ **Documenta**: LLM como alternativa futura (no implementado en v0.1.0)
- ✅ **Incluye**: Diseño experimental completo con matriz de componentes
- ✅ **Incluye**: Trazabilidad básica PROV-O (wasDerivedFrom)
- ❌ **NO incluye**: Implementaciones LLM (v0.2.0+)
- ❌ **NO incluye**: Resultados experimentales completos (solo diseño)
- ❌ **NO incluye**: PROV-O completo avanzado (solo básico)

---

---

## 📋 Consolidación de Documentación

**Ver plan detallado**: `article/CONSOLIDACION_DOCS.md`  
**Notas de release**: Ver `RELEASE_NOTES.md` (en raíz del proyecto) - Lista de archivos a eliminar y estado del release

### Resumen de Consolidación

**Archivos a Eliminar** (información transferida al PLAN):
- `article/ANALISIS_CODIGO_REFERENCIA.md` ✅
- `article/RESUMEN_AUDITORIA_GAPS.md` ✅
- `docs/theory/GRAPHRAG_AVANZADO.md` (guía futura, no necesario para v0.1.0)

**Archivos a Consolidar**:
- `docs/validation/` → Mantener solo `README.md` y `validation_summary.md`
- `docs/examples/` → Consolidar ejemplos específicos en archivos principales

**Tiempo estimado**: 1.25 horas (después de completar release)

**Criterio**: Mantener solo documentación que aporta valor único para usuarios finales.

---

---

## 🎯 ENFOQUE: SOLO RELEASE v0.1.0

**Este plan se enfoca ÚNICAMENTE en completar el release v0.1.0.**

**Scope v0.1.0**:
- ✅ Implementar `SpacyInferenceService` (NER básico)
- ✅ Completar pipeline ETI con fase Inference básica
- ✅ Documentación científica rigurosa (RQs, definiciones, matriz experimental)
- ✅ Diseño experimental completo (no ejecución)

**Fuera de scope v0.1.0**:
- ❌ Implementación LLM (v0.2.0+)
- ❌ Experimentos ejecutados (solo diseño)
- ❌ PROV-O completo avanzado (solo básico)

---

**Última actualización**: 2025-01-XX
**Versión objetivo**: Release v0.1.0 con ETI completo (spaCy NER-only) + diseño experimental
**Closure**: Implementación única con spaCy, LLM documentado como alternativa futura

**Estado del Release**: ✅ **IMPLEMENTACIÓN Y DOCUMENTACIÓN COMPLETAS**
- ✅ Todas las tareas de implementación (Prioridad 0) completadas
- ✅ Todas las tareas de documentación (Prioridades 1-5) completadas
- ⏳ Solo falta validación final (ejecutar pipeline end-to-end, verificar persistencia, ejecutar tests)

---

## 📝 Nota sobre Implementación LLM (v0.2.0+ - FUERA DE SCOPE v0.1.0)

**Estado**: Código de referencia evaluado y documentado para futuras versiones.

**Para v0.1.0**: Solo se implementa `SpacyInferenceService` (NER básico). 
La implementación LLM queda para v0.2.0+ y está documentada en el código como alternativa futura.

**Referencia**: Neo4j LLM Graph Builder
- URL: https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/
- El código en `reference_code/` proporciona base para futura implementación de `LLMInferenceService`

