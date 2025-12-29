# Ungraph — Investigación técnico-científica

**Resumen:**
Las arquitecturas modernas de Retrieval-Augmented Generation (RAG) enfrentan desafíos en la construcción de grafos de conocimiento confiables y trazables. Este trabajo propone el patrón Extract-Transform-Inference (ETI) como evolución del tradicional ETL, añadiendo una fase explícita de inferencia que genera hechos normalizados con trazabilidad PROV-O. 

Presentamos una implementación parcial de ETI en la librería Ungraph, que construye Lexical Graphs sobre Neo4j integrando chunking estratégico, embeddings vectoriales y patrones GraphRAG básicos. La implementación actual cubre las fases Extract y Transform; la fase Inference se implementa mediante extracción transductiva básica de entidades nombradas (NER) usando spaCy, generando facts simples de mención y relaciones de co-ocurrencia.

El diseño experimental propone evaluar la efectividad mediante experimentos reproducibles en cuatro dominios (financiero, biomédico, científico y general), comparando pipelines control (ET) versus ETI en métricas de recuperación (recall@k, MRR), calidad de QA (F1), precisión de inferencia y tasa de hallucination. Los resultados experimentales completos están pendientes de ejecución.

El patrón ETI proporciona un marco coherente para construir sistemas de conocimiento confiables, integrando principios de ingeniería del conocimiento, Web semántica (ontologías, PROV) y neuro-symbolic computing.

## Objetivo
Formalizar y documentar, con rigor científico y reproducible, los experimentos y resultados que soportan las decisiones de diseño de Ungraph (estrategias de chunking, pipelines híbridos de recuperación, uso de Neo4j como almacén vectorial vs alternativas, y la ontología propuesta para `File`/`Page`/`Chunk`).

## Alcance de la investigación
- Evaluaciones empíricas de estrategias de chunking (fixed-size, lexical, semantic, hierarchical) por dominio (financiero, biomedicina, papers científicos, negocio).  
- Comparación de estrategias de recuperación: vector-only, text-only, hybrid, hybrid + graph expansion + LM reranker.  
- Benchmarks de indexación/vector search: Neo4j vector indexes vs FAISS/Milvus/Weaviate (latencia, recall, coste).  
- Formalización ontológica (`File`, `Page`, `Chunk`) y mapeos a vocabularios estándar (schema.org, PROV-O).  
- Reproducibilidad: scripts, Opik experiment configs y OpenAI Evals para evaluaciones model-graded y human-in-the-loop.

## Metodología (resumen)
1. Preparación de datasets (EDGAR/financial filings, BioASQ/PubMedQA, arXiv subsets, internal SOPs).  
2. Implementación de variantes (chunkers, retrievers, pattern execution).  
3. Ejecución de experimentos E1–E4 con harness Opik y registro de métricas (recall@k, MRR, QA-F1, inference accuracy, hallucination rate, latency).  
4. Análisis estadístico y reporte reproducible (notebooks, tablas y gráficos).

## Research Questions e Hipótesis

### Research Questions

**RQ1: Efectividad de la Fase de Inferencia**
¿Añadir una fase explícita de inferencia (I) mejora la calidad de recuperación y respuesta de preguntas comparado con pipelines que solo realizan extracción y transformación (ET)?

**RQ2: Tipos de Inferencia por Dominio**
¿Qué tipo de inferencia (LM-only, symbolic-only, neuro-symbolic) es más efectiva para diferentes dominios de conocimiento (financiero, biomédico, científico, general)?

**RQ3: Trade-off Trazabilidad vs Performance**
¿La trazabilidad completa con PROV-O mejora la confianza y explicabilidad del sistema sin sacrificar significativamente el rendimiento (latencia, throughput)?

**Nota**: Estas research questions guiarán los experimentos futuros una vez completada la implementación de la fase Inference. Para v0.1.0, se implementa solo extracción transductiva básica (NER con spaCy); las capacidades avanzadas de inferencia están planificadas para v0.2+.

### Hipótesis Experimentales

- **H1**: ETI (con Inference) > ET (sin Inference) en recall@k y QA-F1
- **H2**: Semantic chunking > Recursive chunking para dominios técnicos
- **H3**: Parent-Child retrieval > Basic retrieval para preguntas que requieren contexto
- **H4**: [Futuro] Hybrid inference > LM-only para precisión de facts extraídos

### Metodología experimental — Protocolo reproducible 🧪

**Objetivo:** Definir un protocolo replicable paso a paso para ejecutar y evaluar comparativas entre pipelines control (ET) y ETI y sus variantes (LM‑only, symbolic‑only, neuro‑symbolic). Todas las ejecuciones deben grabar metadatos de entorno, seeds y bundles PROV para trazabilidad.

1) Entorno reproducible
- Usar entorno virtual (`python -m venv .venv` o Conda) y fijar Python (ej. 3.11). Ejecutar `pip freeze > requirements.txt` y capturar el hash de commit: `git rev-parse --short HEAD`.
- Registrar: SO, versiones de paquetes, URI de bases (Neo4j), OPIK env var present (no incluir llaves en artefactos), y `RANDOM_SEED` en env.

2) Adquisición y preparación de datasets
- EDGAR/10‑K: script `scripts/fetch_edgar.py --out data/edgar/` (parseo, segmentación por secciones).  
- BioASQ/PubMedQA: usar dumps oficiales o APIs; almacenar en `data/biomed/` con manifest JSON (sha256 checksums).  
- arXiv subsets: extraer por query (arXiv category) y guardar metadatos.  
- Generar tabla `experiments/datasets.csv` (placeholder) con columnas: dataset, URL, license, n_documents, n_chunks_estimated, notes.

3) Definir pipelines y variantes
- Pipelines: ET (Extract + Transform) y ETI (Extract + Transform + Inference).  
- Variantes de inferencia: `lm-only`, `symbolic-only`, `neuro-symbolic`.
- Implementar cada pipeline como un `dag` reproducible; los configs estarán en `experiments/<domain>/<pipeline>.yaml`.

4) Configuración Opik (plantilla)
- Crear `experiments/finance/etik_finance_opik.yaml` con placeholders. No incluir OPIK_API_KEY en repositorio; usar variables de entorno.

Ejemplo (plantilla, no incluir secretos):

```yaml
experiment_name: finance_eti_v1
dataset: edgar
pipeline: ETI
inference: lm-only
opik:
  api_key: ${OPIK_API_KEY}
  model: openai-xyz
  timeout: 60
seeds:
  random_seed: 42
output:
  dir: experiments/finance_eti_v1/
```

5) Ejecución (comandos reproducibles)
- Ejemplo: `python scripts/run_experiment.py --config experiments/finance/finance_eti_v1.yaml --seed 42 --out experiments/finance_eti_v1/`
- Cada ejecución debe escribir un `metadata.json` con: seed, git_hash, timestamp, pipeline, config path, host, package versions.

6) Salida y artefactos
- Guardar: embeddings (binary/ndjson), `chunks.jsonl`, `inferred_facts.jsonl` (tripletas), `prov_bundle.json` (PROV), `evaluation/` con outputs y logs.
- Los hechos inferidos deben incluir campos: subject, predicate, object, confidence, provenance_ref.

7) Métricas y evaluación automática
- Recuperación: recall@k, MRR.  
- QA: F1 (micro/macro) sobre conjuntos anotados.  
- Inferencia: precision, recall, F1 sobre facts anotados (TP/FP/FN).  
- Hallucination rate: proportion of generated facts judged as ungrounded by annotators.  
- Coherencia de grafo: medidas de inconsistencia (contradicciones) y cobertura de ontología.
- Definir scripts en `scripts/evaluate.py --pred inferred_facts.jsonl --gold gold_facts.jsonl --metrics all`.

8) Evaluación humana (protocolo)
- Sampling: seleccionar N facts por pipeline (stratificado por confianza y dominio).  
- Instrucciones de anotadores: verificar si el hecho está explícito/entailed por la fuente y marcar fuente URL/loc.
- Medir inter-annotator agreement (Cohen's kappa) y adjudicar desacuerdos.

9) Análisis estadístico
- Comparar pares (ET vs ETI) usando bootstrap resampling para intervalos de confianza y test de hipótesis (paired t-test o Wilcoxon según normalidad). Reportar p‑values y tamaño de efecto (Cohen's d).

10) Publicación y reproducibilidad
- Publicar notebooks (convertir a HTML con `jupyter nbconvert --to html`) y subir a `docs/` y GitHub (tagged release). Registrar DOI en Zenodo para la release con los notebooks y datasets que puedan compartirse.
- Incluir `experiments/<id>/prov_bundle.json` para que terceros puedan auditar derivaciones.

> Nota: Las plantillas de configs y scripts estarán en `experiments/templates/` y se actualizarán con cada revisión; **no** se publicarán resultados hasta ejecutar los experimentos y validar las métricas con los oráculos y evaluaciones humanas.

  

## Entregables esperados
- Documento final con: motivación, estado del arte, metodología, resultados experimentales, discusión, limitaciones y recomendaciones.  
- Ficheros reproducibles (scripts, Opik configs, eval templates), notebooks y datasets anotados.  
- Ontología publicada (`docs/ontology.md` + `ontology.owl` + JSON-LD examples).

## Relación con las tareas del proyecto
Esta tarea final está registrada en el checklist maestro `_NET_STEPS.md` (ver `project/Instructions/_NET_STEPS.md`) como la tarea de documentación técnico-científica que culmina el ciclo de investigación y desarrollo. Debe incluir todas las referencias y evidencia recogida en la fase de evaluación.

## Referencias (iniciales)
- Lewis et al. [1] - RAG (Retrieval-Augmented Generation)
- Peng et al. [2] - GraphRAG Survey
- Neo4j GraphRAG Patterns Catalog [3]
- W3C PROV [4] - Provenance y trazabilidad
- Zhong et al. [5] - Surveys de construcción de KG
- d'Avila Garcez et al. [6] - Neuro-Symbolic Computing
- Rowley [7], Ackoff [8], Zins [9] - DIKW Hierarchy
- Miller 1956 [10]; Thalmann et al. 2019 [11] (chunking)

## Patrón: Extracción — Transformación — Inferencia (ETI)

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

### Comparación ETL vs ETI

| Aspecto | ETL (Tradicional) | ETI (Propuesto) |
|---------|-------------------|-----------------|
| **Fases** | Extract, Transform, Load | Extract, Transform, **Infer** |
| **Objetivo** | Preparar datos para almacenamiento | Construir conocimiento trazable |
| **Artefactos** | Datos estructurados | Facts, relaciones, explicaciones |
| **Trazabilidad** | Limitada (metadatos básicos) | Completa (PROV-O) |
| **Validación** | Verificación de formato | Validación de conocimiento |
| **Razonamiento** | No incluye | Incluye inferencia explícita |

**Descripción:**
El patrón *Extracción — Transformación — Inferencia* (ETI) se propone como la evolución natural del clásico ETL en el contexto de la ingeniería del conocimiento y de las arquitecturas GraphRAG. ETI articula tres fases obligatorias en pipelines de conocimiento: 1) **Extracción** de fuentes crudas y metadatos; 2) **Transformación** mediante chunking, normalización, enriquecimiento semántico y linking; 3) **Inferencia** donde modelos (LM/ML/razonadores simbólicos) generan hechos, relaciones, deducciones y explicaciones que alimentan los grafos y los índices vectoriales.

**Justificación y posición en el artículo:**
Esta hipótesis es central para la investigación: defendemos que añadir una fase explícita de inferencia (no meramente transductiva) distingue las soluciones de *knowledge engineering* modernas de los pipelines ETL tradicionales y mejora la calidad y utilidad de los artefactos (embeddings, nodos/aristas, tripletas). La hipótesis **no debe eliminarse**: será validada mediante experimentos y ablations en los que compararemos pipelines con y sin la fase de inferencia.

**Arquitectura propuesta y artefactos:**
- Extracción: parsers y connectors que producen `File`/`Page` y metadatos (timestamps, autoría, contexto).  
- Transformación: chunkers (fixed, lexical, hierarchical, semantic), normalizadores, detectores de idioma, y generadores de embeddings; salida: `Chunk` con anotaciones semánticas.  
- Inferencia: modelos que extraen relaciones/facts, resuelven ambigüedad, hacen mapping a la ontología (`File`/`Page`/`Chunk`), y generan aristas y propiedades para el grafo; salida: nodos, aristas, tripletas RDF/JSON-LD y señales de confianza.

**Estado de Implementación (v0.1.0):**
La implementación actual de Ungraph incluye una fase de inferencia básica que realiza extracción transductiva de entidades nombradas (NER) mediante spaCy. Esta fase genera facts simples de mención `(chunk_id, "MENTIONS", entity_name)` y relaciones básicas de co-ocurrencia. **Nota importante**: Esta implementación es un primer paso hacia inferencia no transductiva completa. Las capacidades avanzadas de inferencia (resolución de ambigüedad, normalización de entidades, relaciones semánticas complejas, razonamiento sobre el grafo) están planificadas para versiones futuras (v0.2+) y serán validadas experimentalmente como parte de la investigación propuesta.

**Ejemplo (finanzas):**
1. Extracción: descarga y parseo de 10‑K/EDGAR.  
2. Transformación: chunking por secciones y extracción de tablas, embeddings por chunk.  
3. Inferencia: LM que extrae hechos financieros (ingresos, activos) y relaciones (empresa‑subsidiaria), normaliza entidades y crea/actualiza nodos y relaciones en el grafo.

**Clarificación: Extracción vs Inferencia**

Es importante distinguir entre extracción transductiva e inferencia no transductiva:

- **Extracción transductiva** (implementada en v0.1.0): Identifica entidades explícitas en el texto mediante NER. Ejemplo: "Apple Inc." aparece en texto → Entity "Apple Inc." con tipo ORGANIZATION. Esta es una operación de reconocimiento de patrones que no genera conocimiento nuevo.

- **Inferencia no transductiva** (planificada para v0.2+): Deduce relaciones implícitas, resuelve ambigüedad mediante contexto, normaliza variantes de entidades, y genera conocimiento nuevo mediante razonamiento. Ejemplos:
  - Resolución de ambigüedad: "Apple" en contexto financiero → ORGANIZATION (no FRUIT)
  - Normalización: "Apple Inc.", "Apple", "AAPL" → misma entidad normalizada
  - Relaciones semánticas: "Tim Cook lidera Apple" → WORKS_FOR(Tim Cook, Apple), CEO_OF(Tim Cook, Apple)
  - Razonamiento transitivo: Si A → B y B → C, entonces A → C

La implementación actual (v0.1.0) realiza extracción transductiva básica. La inferencia no transductiva completa será implementada y validada experimentalmente en versiones futuras.

**Medición y evaluación experimental:**
Evaluaremos ETI mediante métricas clásicas y específicas: recall@k y MRR en tareas de recuperación, QA‑F1 en pipelines RAG, *inference accuracy* (precisión/recall sobre hechos extraídos), tasa de *hallucination*, coherencia de grafo y coste/latencia. Proponemos estudios de ablation (sin inferencia vs con inferencia) para cuantificar su impacto en las tareas downstream.

**Relación con otros componentes del estudio:**
ETI conecta directamente con: estrategias de chunking (fase Transformación), patrones GraphRAG (uso de grafos y expansión), la ontología `File`/`Page`/`Chunk` y las evaluaciones reproducibles (notebooks y Opik configs). Las decisiones implementadas en Ungraph (ingestores, chunkers, retrievers) están diseñadas para soportar y evaluar ETI.

## Filosofía y justificación epistemológica del ETI

**Resumen filosófico:**
ETI toma como punto de partida clásicas reflexiones sobre la transición *data → information → knowledge* (DIKW; Ackoff [8]; Rowley [7]; Zins [9]) y propone transformar los pipelines de preparación de datos en procesos que explícitamente construyen artefactos justificables y utilizables para razonamiento automático (con fiabilidad y trazabilidad). En términos epistemológicos, ETI busca convertir información estructurada (estructuras y anotaciones) en *creencias justificadas* (hechos, relaciones y reglas) que puedan sostener inferencias y decisiones automatizadas.

**Apoyos bibliográficos clave:**
- DIKW y los debates sobre la naturaleza de conocimiento (Ackoff [8]; Rowley [7]; Zins [9]) muestran la necesidad de procesos que no sólo estructuren datos sino que produzcan conocimiento justificable (ver discusión DIKW y críticas). (véase: DIKW reviews, 1989–2007).  
- Provenance y trazabilidad (W3C PROV [4]) son esenciales para que las inferencias sean evaluables, reproducibles y confiables; PROV formaliza cómo representar entidades, actividades y agentes involucrados en la construcción de hechos (W3C PROV, 2013).
- Workflows de construcción de Knowledge Graphs muestran que la comunidad distingue etapas (IE → KBC → KG refinement) y discute la integración de extracción y razonamiento [5].
- RAG [1] y GraphRAG [2] muestran que integrar memoria no‑paramétrica y grafos mejora el grounding factual y reduce la tasa de hallucination; ETI extiende estos enfoques al incorporar una fase explícita de inferencia que genera relaciones verificadas y trazables.
- Neuro‑symbolic surveys [6] justifican el valor de combinar modelos estadísticos (LMs) con razonamiento simbólico para obtener explicabilidad y control sobre inferencias.

**Argumento metodológico y experimental (resumen):**
1. Hipótesis: añadir una fase de inferencia que produzca hechos normalizados y con trazabilidad mejora la utilidad de los artefactos de conocimiento (mayor precision/recall en QA y recuperación, menor tasa de hallucination y mayor coherencia de grafo).  
2. Protocolo: definir pipelines control (ET, no I) vs ETI y medir: inference accuracy (micro/macro), downstream QA‑F1, recall@k, MRR, hallucination rate, y métricas de trazabilidad/provenance coverage (PROV con mediciones cuantificables).  
3. Ablations: tipos de inferencia (LM-only, symbolic-only, neuro-symbolic) y su impacto; evaluación por dominio (finanzas, biomedicina, papers científicos) y por nivel de confianza.

**Criterios de rigor científico:**
- Usar datasets públicos y reproducibles, scripts y configs Opik, Evals automáticos y evaluaciones humanas para facts críticos; publicar notebooks y JSON-LD/PROV outputs para verificación externa.  
- Auditar inferencias contra oráculos o conjuntos anotados (fact‑level labels) y reportar intervalos de confianza y análisis de error (tipo de error: omisión vs comisión/hallucination).

**Impacto conceptual:**
ETI emerge como patrón que combina principios de la ingeniería del conocimiento, la Web semántica (ontologías y PROV), y prácticas modernas de ML/LM (RAG/GraphRAG, neuro‑symbolic), ofreciendo un marco coherente para construir *sistemas de conocimiento confiables y explicables*.

---

*Estado:* Esta página contiene ahora la descripción de alcance y la estructura que seguirá el trabajo científico; el borrador final se completará después de ejecutar los experimentos y consolidar resultados (ver `_NET_STEPS.md` para seguimiento).

## Estructura del artículo y placeholders de resultados

Para que este documento mantenga un estilo y rigor académico (tipo paper científico), se ha reescrito la organización como sigue. **Importante:** no se inventan resultados; todas las secciones marcadas como *Resultados* o *Hallazgos* contienen placeholders que serán completados solamente tras la ejecución de los experimentos reproducibles y la recolección de métricas.

1. Introducción y motivación — exposición del problema y la hipótesis ETI (ya incluida).  
2. Estado del arte — revisión de RAG/GraphRAG, DIKW, provenance y técnicas de construcción de KGs (referencias a continuación).  
3. Diseño del patrón ETI — definición formal, arquitectura, artefactos y casos de uso (sección ETI).  
4. Metodología experimental — datasets (EDGAR/10‑K, BioASQ/PubMedQA, arXiv subsets, SOPs), configuraciones (Opik), pipelines (ET, ETI, variantes neuro‑simbólicas), métricas y criterios de evaluación.  
   - *Placeholders:* tablas con descripción de datasets y configuraciones de experimentos (TBD).

### Diseño Experimental: Matriz de Componentes

Para evaluar el patrón ETI, diseñamos un espacio experimental multidimensional que combina diferentes componentes disponibles en Ungraph:

**Componentes del Espacio Experimental:**

- **Chunking**: {recursive, semantic, lexical, hierarchical}
- **Embedding**: {all-MiniLM-L6-v2, otros modelos HuggingFace}
- **Retrieval**: {basic, parent_child, hybrid, graph_enhanced_vector}
- **Inference**: {none, ner-only} (v0.1.0 implementa solo ner-only con spaCy)
- **Domain**: {finance, biomedical, scientific, general}

**Matriz de Experimentos Prioritarios:**

| ID | Chunking | Embedding | Retrieval | Inference | Domain | Prioridad |
|----|----------|-----------|-----------|-----------|--------|-----------|
| E1 | `recursive` | `all-MiniLM-L6-v2` | `basic` | `ner-only` | `finance` | 🔴 Alta |
| E2 | `recursive` | `all-MiniLM-L6-v2` | `parent_child` | `ner-only` | `finance` | 🔴 Alta |
| E3 | `semantic` | `all-MiniLM-L6-v2` | `hybrid` | `ner-only` | `biomedical` | 🟡 Media |
| E4 | `lexical` | `all-MiniLM-L6-v2` | `graph_enhanced_vector` | `ner-only` | `scientific` | 🟡 Media |
| E5 | `hierarchical` | `all-MiniLM-L6-v2` | `community_summary` | `ner-only` | `general` | 🟢 Baja |

**Ablation Studies (Control vs ETI):**

| Baseline | Variante | Diferencia | Objetivo |
|----------|----------|------------|----------|
| ET (sin I) | ETI (con I) | Fase Inference | Medir impacto de inferencia |
| `basic` retrieval | `parent_child` | Patrón retrieval | Medir impacto de contexto |
| `recursive` chunking | `semantic` chunking | Estrategia chunking | Medir impacto de chunking |

**Nota**: Para release v0.1.0, solo se implementa `ner-only` (spaCy). Implementaciones LLM (`lm-only`, `hybrid`) están documentadas como alternativas futuras (v0.2+) y serán validadas experimentalmente.  
5. Experimentos y resultados — comparativas control/ETI y ablations (LM‑only, symbolic‑only, neuro‑symbolic).  
   - *Resultados (placeholder):* (i) inference accuracy — TBD; (ii) QA‑F1 y recall@k — TBD; (iii) tasas de hallucination y coste/latencia — TBD.  
6. Discusión y limitaciones — análisis cualitativo de errores, impacto de trazabilidad (PROV) y consideraciones éticas.  
7. Conclusiones y trabajos futuros — validación de la hipótesis ETI y roadmap experimental.

> Nota: Todas las figuras, tablas y valores numéricos se incluirán solamente después de ejecutar los experimentos mencionados y compilar los notebooks/Opik configs reproducibles. No se añadirá ninguna cifra hasta ese momento.

## Referencias

1. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., & Riedel, S. (2020). Retrieval‑Augmented Generation for Knowledge‑Intensive NLP Tasks. arXiv:2005.11401. https://arxiv.org/abs/2005.11401

2. Peng, B., Zhu, Y., Liu, Y., Bo, X., Shi, H., Hong, C., & Tang, S. (2024). Graph Retrieval‑Augmented Generation: A Survey. arXiv:2408.08921. https://arxiv.org/abs/2408.08921

3. Neo4j, Inc. (2024). GraphRAG Patterns Catalog. https://graphrag.com/reference/

4. W3C Provenance Working Group. (2013). PROV‑Overview. W3C Note. https://www.w3.org/TR/prov-overview/

5. Zhong, L., Wu, J., Li, Q., & Peng, H. (2023). A Comprehensive Survey on Automatic Knowledge Graph Construction. arXiv:2302.05019. https://arxiv.org/abs/2302.05019

6. d'Avila Garcez, A., Gori, M., Lamb, L. C., Serafini, L., Spranger, M., & Tran, S. N. (2019). Neural‑Symbolic Computing: An Effective Methodology for Principled Integration of Machine Learning and Reasoning. arXiv:1905.06088. https://arxiv.org/abs/1905.06088

7. Rowley, J. (2007). The Wisdom Hierarchy: Representations of the DIKW Hierarchy. Journal of Information & Communication Science. https://doi.org/10.1177/0165551506070706

8. Ackoff, R. (1989). From Data to Wisdom. Journal of Applied Systems Analysis.

9. Zins, C. (2007). Conceptual Approaches for Defining Data, Information, and Knowledge. Journal of the American Society for Information Science and Technology, 58(4), 479–493. https://doi.org/10.1002/asi.20508

10. Miller, G. A. (1956). The Magical Number Seven, Plus or Minus Two: Some Limits on Our Capacity for Processing Information. Psychological Review, 63(2), 81–97. https://doi.org/10.1037/h0043158

11. Thalmann, M., Souza, A. S., & Oberauer, K. (2019). How does chunking help working memory? Journal of Experimental Psychology. https://psycnet.apa.org/record/2018-18179-001

**BibTeX:** `article/references.bib` contiene las entradas BibTeX para las referencias listadas.

**Notas (enlaces directos):**
[1]: https://arxiv.org/abs/2005.11401
[2]: https://arxiv.org/abs/2408.08921
[3]: https://graphrag.com/reference/
[4]: https://www.w3.org/TR/prov-overview/
[5]: https://arxiv.org/abs/2302.05019
[6]: https://arxiv.org/abs/1905.06088
[7]: https://doi.org/10.1177/0165551506070706
[8]: (Ackoff 1989)
[9]: https://doi.org/10.1002/asi.20508
[10]: https://doi.org/10.1037/h0043158
[11]: https://psycnet.apa.org/record/2018-18179-001

---

*Estado:* Se ha añadido la bibliografía en formato APA numerada y un listado de enlaces directos; la BibTeX fuente está disponible en `article/references.bib`. Los placeholders de resultados esperan la ejecución de experimentos reproducibles antes de su completado.