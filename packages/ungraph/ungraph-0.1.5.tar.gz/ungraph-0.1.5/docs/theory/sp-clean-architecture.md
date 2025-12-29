# Clean Architecture

## Principios Fundamentales

Clean Architecture es un enfoque de diseño de software que separa el código en capas concéntricas, donde las capas internas no dependen de las externas.

## Estructura de Capas

```
┌─────────────────────────────────────┐
│         Infrastructure              │  ← Frameworks, DB, APIs externas
├─────────────────────────────────────┤
│         Application                 │  ← Casos de uso
├─────────────────────────────────────┤
│         Domain                      │  ← Entidades, Reglas de negocio
└─────────────────────────────────────┘
```

## Regla de Dependencias

**Las dependencias apuntan hacia adentro:**

- Infrastructure → Application → Domain ✅
- Domain → Infrastructure ❌ PROHIBIDO
- Domain → Application ❌ PROHIBIDO

## Beneficios

1. **Independencia de Frameworks**: El dominio no depende de frameworks externos
2. **Testabilidad**: Fácil crear tests con mocks
3. **Independencia de UI**: La lógica de negocio no depende de la interfaz
4. **Independencia de DB**: Puedes cambiar la base de datos sin afectar el dominio
5. **Independencia de Agentes Externos**: El dominio no conoce APIs externas

## Aplicación en Ungraph

### Domain Layer

```python
# domain/entities/chunk.py
@dataclass
class Chunk:
    id: str
    page_content: str
    # NO conoce Neo4j, LangChain, etc.
```

### Application Layer

```python
# application/use_cases/ingest_document.py
class IngestDocumentUseCase:
    def __init__(
        self,
        chunking_service: ChunkingService,  # Interfaz, no implementación
        chunk_repository: ChunkRepository     # Interfaz, no implementación
    ):
        ...
```

### Infrastructure Layer

```python
# infrastructure/repositories/neo4j_chunk_repository.py
class Neo4jChunkRepository(ChunkRepository):  # Implementa interfaz del dominio
    def __init__(self, driver: GraphDatabase):  # Puede usar Neo4j
        ...
```

## Referencias

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [The Clean Architecture Book](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
