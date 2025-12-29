# Clean Architecture

## Fundamental Principles

Clean Architecture is a software design approach that separates code into concentric layers, where inner layers don't depend on outer ones.

## Layer Structure

```
┌─────────────────────────────────────┐
│         Infrastructure              │  ← Frameworks, DB, External APIs
├─────────────────────────────────────┤
│         Application                 │  ← Use Cases
├─────────────────────────────────────┤
│         Domain                      │  ← Entities, Business Rules
└─────────────────────────────────────┘
```

## Dependency Rule

**Dependencies point inward:**

- Infrastructure → Application → Domain ✅
- Domain → Infrastructure ❌ FORBIDDEN
- Domain → Application ❌ FORBIDDEN

## Benefits

1. **Framework Independence**: Domain doesn't depend on external frameworks
2. **Testability**: Easy to create tests with mocks
3. **UI Independence**: Business logic doesn't depend on the interface
4. **Database Independence**: You can change the database without affecting the domain
5. **External Agent Independence**: Domain doesn't know about external APIs

## Application in Ungraph

### Domain Layer

```python
# domain/entities/chunk.py
@dataclass
class Chunk:
    id: str
    page_content: str
    # Does NOT know about Neo4j, LangChain, etc.
```

### Application Layer

```python
# application/use_cases/ingest_document.py
class IngestDocumentUseCase:
    def __init__(
        self,
        chunking_service: ChunkingService,  # Interface, not implementation
        chunk_repository: ChunkRepository     # Interface, not implementation
    ):
        ...
```

### Infrastructure Layer

```python
# infrastructure/repositories/neo4j_chunk_repository.py
class Neo4jChunkRepository(ChunkRepository):  # Implements domain interface
    def __init__(self, driver: GraphDatabase):  # Can use Neo4j
        ...
```

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [The Clean Architecture Book](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
