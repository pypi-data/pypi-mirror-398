# Arquitectura del Sistema

## Visión General

Ungraph sigue los principios de **Clean Architecture** y **Domain-Driven Design (DDD)** para garantizar mantenibilidad, testabilidad y extensibilidad.

## Estructura de Capas

```
src/
├── domain/              # Capa más interna - NO depende de nada externo
│   ├── entities/        # Entidades de negocio (Chunk, Document, File, Page)
│   ├── value_objects/   # Objetos de valor inmutables (GraphPattern, Embedding)
│   ├── repositories/    # Interfaces (abstracciones) - NO implementaciones
│   └── services/        # Interfaces de servicios del dominio
│
├── application/         # Casos de uso - depende SOLO de domain
│   └── use_cases/       # Orquestación de flujos de trabajo
│
├── infrastructure/      # Implementaciones concretas
│   ├── repositories/    # Implementaciones (Neo4jChunkRepository)
│   └── services/        # Implementaciones (LangChain, HuggingFace, Neo4j)
│
├── core/                # Configuración compartida
│   └── configuration.py # Gestión de configuración global
│
└── utils/               # Utilidades temporales (en proceso de migración)
```

## Principios de Arquitectura

### 1. Regla de Dependencias

**NUNCA** importar desde capas externas hacia capas internas:

```python
# ❌ PROHIBIDO: domain importa de infrastructure
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository

# ✅ CORRECTO: domain solo tiene interfaces
from domain.repositories.chunk_repository import ChunkRepository

# ✅ CORRECTO: infrastructure implementa interfaces de domain
from domain.repositories.chunk_repository import ChunkRepository
class Neo4jChunkRepository(ChunkRepository):
    ...
```

**Dirección de dependencias:**
- `infrastructure` → `application` → `domain` ✅
- `domain` → `infrastructure` ❌ PROHIBIDO
- `domain` → `application` ❌ PROHIBIDO

### 2. Entidades de Dominio

**Características:**
- Usan `@dataclass` para estructuras de datos
- Contienen SOLO datos y lógica de negocio básica
- NO conocen frameworks externos (Neo4j, LangChain, etc.)
- Pueden tener validaciones y métodos de dominio

**Ejemplo:**
```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Chunk:
    id: str
    page_content: str
    metadata: Dict[str, Any]
    
    def get_filename(self) -> str:
        return self.metadata.get('filename')
```

### 3. Value Objects

**Características:**
- Inmutables (`frozen=True`)
- Se comparan por valor, no por referencia
- Validaciones en `__post_init__`
- Sin identidad propia

**Ejemplo:**
```python
@dataclass(frozen=True)
class GraphPattern:
    name: str
    description: str
    node_definitions: List[NodeDefinition]
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Pattern name cannot be empty")
```

### 4. Interfaces (Repositorios y Servicios)

**Ubicación:** `domain/repositories/` y `domain/services/`

**Características:**
- Usan `ABC` (Abstract Base Class) con `@abstractmethod`
- Definen QUÉ operaciones se necesitan, no CÓMO
- Están en el dominio porque el dominio define sus necesidades

**Ejemplo:**
```python
from abc import ABC, abstractmethod
from domain.entities.chunk import Chunk

class ChunkRepository(ABC):
    @abstractmethod
    def save(self, chunk: Chunk) -> None:
        pass
```

### 5. Implementaciones Concretas

**Ubicación:** `infrastructure/repositories/` y `infrastructure/services/`

**Características:**
- Implementan interfaces del dominio
- Pueden usar cualquier framework (Neo4j, LangChain, etc.)
- Son intercambiables (puedes tener múltiples implementaciones)

**Ejemplo:**
```python
from domain.repositories.chunk_repository import ChunkRepository
from domain.entities.chunk import Chunk
from neo4j import GraphDatabase

class Neo4jChunkRepository(ChunkRepository):
    def __init__(self, driver: GraphDatabase):
        self.driver = driver
    
    def save(self, chunk: Chunk) -> None:
        # Implementación usando Neo4j
        ...
```

### 6. Casos de Uso

**Ubicación:** `application/use_cases/`

**Características:**
- Dependen SOLO de interfaces del dominio
- Orquestan el flujo de trabajo
- Reciben dependencias por inyección (no las crean)
- Son fáciles de testear (mockeas las dependencias)

**Ejemplo:**
```python
from domain.entities.chunk import Chunk
from domain.repositories.chunk_repository import ChunkRepository
from domain.services.chunking_service import ChunkingService

class IngestDocumentUseCase:
    def __init__(
        self,
        chunking_service: ChunkingService,  # Interfaz
        chunk_repository: ChunkRepository     # Interfaz
    ):
        self.chunking_service = chunking_service
        self.chunk_repository = chunk_repository
    
    def execute(self, document: Document) -> List[Chunk]:
        chunks = self.chunking_service.chunk(document)
        self.chunk_repository.save_batch(chunks)
        return chunks
```

### 7. Composition Root

**Ubicación:** `application/dependencies.py`

**Responsabilidad:** Crear y configurar todas las dependencias

**Ejemplo:**
```python
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository
from infrastructure.services.langchain_chunking_service import LangChainChunkingService
from application.use_cases.ingest_document import IngestDocumentUseCase
from src.utils.graph_operations import graph_session

def create_ingest_document_use_case() -> IngestDocumentUseCase:
    """Factory: crea y configura el caso de uso"""
    driver = graph_session()
    repository = Neo4jChunkRepository(driver)
    chunking_service = LangChainChunkingService()
    
    return IngestDocumentUseCase(
        chunking_service=chunking_service,
        chunk_repository=repository
    )
```

## Ventajas de esta Arquitectura

1. **Testabilidad**: Fácil crear mocks de las interfaces
2. **Mantenibilidad**: Separación clara de responsabilidades
3. **Extensibilidad**: Fácil agregar nuevas implementaciones
4. **Independencia**: El dominio no depende de frameworks externos
5. **Flexibilidad**: Puedes cambiar implementaciones sin afectar el dominio

## Referencias

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
