# System Architecture

## Overview

Ungraph follows **Clean Architecture** and **Domain-Driven Design (DDD)** principles to ensure maintainability, testability, and extensibility.

## Layered Structure

```
src/
├── domain/              # Innermost layer - NO external dependencies
│   ├── entities/        # Business entities (Chunk, Document, File, Page)
│   ├── value_objects/   # Immutable value objects (GraphPattern, Embedding)
│   ├── repositories/    # Interfaces (abstractions) - NO implementations
│   └── services/        # Domain service interfaces
│
├── application/         # Use cases - depends ONLY on domain
│   └── use_cases/       # Workflow orchestration
│
├── infrastructure/      # Concrete implementations
│   ├── repositories/    # Implementations (Neo4jChunkRepository)
│   └── services/        # Implementations (LangChain, HuggingFace, Neo4j)
│
├── core/                # Shared configuration
│   └── configuration.py # Global configuration management
│
└── utils/               # Temporary utilities (being migrated)
```

## Architecture Principles

### 1. Dependency Rule

**NEVER** import from outer layers into inner layers:

```python
# ❌ FORBIDDEN: domain imports from infrastructure
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository

# ✅ CORRECT: domain only has interfaces
from domain.repositories.chunk_repository import ChunkRepository

# ✅ CORRECT: infrastructure implements domain interfaces
from domain.repositories.chunk_repository import ChunkRepository
class Neo4jChunkRepository(ChunkRepository):
    ...
```

**Dependency direction:**
- `infrastructure` → `application` → `domain` ✅
- `domain` → `infrastructure` ❌ FORBIDDEN
- `domain` → `application` ❌ FORBIDDEN

### 2. Domain Entities

**Characteristics:**
- Use `@dataclass` for data structures
- Contain ONLY data and basic business logic
- Do NOT know external frameworks (Neo4j, LangChain, etc.)
- May include validations and domain methods

**Example:**
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

**Characteristics:**
- Immutable (`frozen=True`)
- Compared by value, not by reference
- Validations in `__post_init__`
- No identity of their own

**Example:**
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

### 4. Interfaces (Repositories and Services)

**Location:** `domain/repositories/` and `domain/services/`

**Characteristics:**
- Use `ABC` (Abstract Base Class) with `@abstractmethod`
- Define WHAT operations are needed, not HOW
- Are in domain because the domain defines its needs

**Example:**
```python
from abc import ABC, abstractmethod
from domain.entities.chunk import Chunk

class ChunkRepository(ABC):
    @abstractmethod
    def save(self, chunk: Chunk) -> None:
        pass
```

### 5. Concrete Implementations

**Location:** `infrastructure/repositories/` and `infrastructure/services/`

**Characteristics:**
- Implement domain interfaces
- May use any framework (Neo4j, LangChain, etc.)
- Are interchangeable (you can have multiple implementations)

**Example:**
```python
from domain.repositories.chunk_repository import ChunkRepository
from domain.entities.chunk import Chunk
from neo4j import GraphDatabase

class Neo4jChunkRepository(ChunkRepository):
    def __init__(self, driver: GraphDatabase):
        self.driver = driver
    
    def save(self, chunk: Chunk) -> None:
        # Implementation using Neo4j
        ...
```

### 6. Use Cases

**Location:** `application/use_cases/`

**Characteristics:**
- Depend ONLY on domain interfaces
- Orchestrate the workflow
- Receive dependencies via injection (do not create them)
- Easy to test (mock dependencies)

**Example:**
```python
from domain.entities.chunk import Chunk
from domain.repositories.chunk_repository import ChunkRepository
from domain.services.chunking_service import ChunkingService

class IngestDocumentUseCase:
    def __init__(
        self,
        chunking_service: ChunkingService,  # Interface
        chunk_repository: ChunkRepository     # Interface
    ):
        self.chunking_service = chunking_service
        self.chunk_repository = chunk_repository
    
    def execute(self, document: Document) -> List[Chunk]:
        chunks = self.chunking_service.chunk(document)
        self.chunk_repository.save_batch(chunks)
        return chunks
```

### 7. Composition Root

**Location:** `application/dependencies.py`

**Responsibility:** Create and configure all dependencies

**Example:**
```python
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository
from infrastructure.services.langchain_chunking_service import LangChainChunkingService
from application.use_cases.ingest_document import IngestDocumentUseCase
from src.utils.graph_operations import graph_session

def create_ingest_document_use_case() -> IngestDocumentUseCase:
    """Factory: creates and configures the use case"""
    driver = graph_session()
    repository = Neo4jChunkRepository(driver)
    chunking_service = LangChainChunkingService()
    
    return IngestDocumentUseCase(
        chunking_service=chunking_service,
        chunk_repository=repository
    )
```

## Benefits of this Architecture

1. **Testability**: Easy to create mocks of interfaces
2. **Maintainability**: Clear separation of responsibilities
3. **Extensibility**: Easy to add new implementations
4. **Independence**: Domain does not depend on external frameworks
5. **Flexibility**: You can change implementations without affecting the domain

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
