# Instalación de Inferencia con spaCy

## Instalación Básica

Para usar la fase de inferencia del patrón ETI, necesitas instalar spaCy y los modelos de idioma correspondientes.

### Instalación con extras de Ungraph

```bash
# Instalación básica de spaCy (sin modelos)
pip install ungraph[infer]

# Instalación con modelo de inglés
pip install ungraph[infer-en]
python -m spacy download en_core_web_sm

# Instalación con modelo de español
pip install ungraph[infer-es]
python -m spacy download es_core_news_sm

# Instalación con ambos idiomas
pip install ungraph[infer-all]
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm
```

### Modelos de spaCy Disponibles

**Inglés:**
- `en_core_web_sm` (pequeño, rápido) - Recomendado para desarrollo
- `en_core_web_md` (mediano, más preciso)
- `en_core_web_lg` (grande, más preciso)

**Español:**
- `es_core_news_sm` (pequeño, rápido) - Recomendado para desarrollo
- `es_core_news_md` (mediano, más preciso)
- `es_core_news_lg` (grande, más preciso)

## Uso en Código

### Usar inferencia con idioma específico

```python
from application.dependencies import create_ingest_document_use_case

# Inferencia en inglés (default)
use_case = create_ingest_document_use_case(
    enable_inference=True,
    inference_language="en"  # Usa en_core_web_sm
)

# Inferencia en español
use_case = create_ingest_document_use_case(
    enable_inference=True,
    inference_language="es"  # Usa es_core_news_sm
)

# Usar modelo específico
use_case = create_ingest_document_use_case(
    enable_inference=True,
    inference_model="es_core_news_md"  # Modelo mediano de español
)
```

### Usar directamente SpacyInferenceService

```python
from infrastructure.services.spacy_inference_service import SpacyInferenceService
from domain.entities.chunk import Chunk

# Crear servicio con modelo de inglés
service_en = SpacyInferenceService(model_name="en_core_web_sm")

# Crear servicio con modelo de español
service_es = SpacyInferenceService(model_name="es_core_news_sm")

# Extraer entidades y facts
chunk = Chunk(...)
entities = service_es.extract_entities(chunk)
facts = service_es.infer_facts(chunk)
```

## Notas

- Los modelos de spaCy se descargan por separado después de instalar spaCy
- Los modelos pequeños (`*_sm`) son suficientes para la mayoría de casos de uso
- Los modelos grandes (`*_lg`) proporcionan mayor precisión pero requieren más memoria
- Si spaCy no está instalado, el pipeline funcionará sin fase Inference (solo ET)




