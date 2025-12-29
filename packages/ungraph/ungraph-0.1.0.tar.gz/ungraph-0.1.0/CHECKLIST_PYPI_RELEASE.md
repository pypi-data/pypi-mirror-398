# Checklist para Publicación en PyPI Oficial

Este documento contiene todas las validaciones que deben realizarse antes de publicar `ungraph` en PyPI oficial.

## 📋 Resumen de Estrategia

- **TestPyPI**: Publicar como `ungraphx` (porque `ungraph` ya existe en TestPyPI)
- **PyPI Oficial**: Publicar como `ungraph` (nombre disponible)

---

## ✅ Fase 1: Validaciones Pre-Build

### 1.1 Configuración del Proyecto

- [ ] **pyproject.toml** tiene `name = "ungraph"` (para PyPI oficial)
- [ ] **Versión correcta**: `version = "0.1.0"`
- [ ] **README.md** existe y está completo
- [ ] **LICENSE** existe (MIT)
- [ ] **Descripción** del proyecto es clara y concisa
- [ ] **Keywords** son relevantes y útiles
- [ ] **Classifiers** son correctos (Development Status, License, Python version)
- [ ] **Authors** están correctamente especificados
- [ ] **Requires-python** es `>=3.12`

### 1.2 Estructura del Paquete

- [ ] Todos los módulos en `src/` están listados en `[tool.hatch.build.targets.wheel]`:
  - [ ] `src/domain`
  - [ ] `src/application`
  - [ ] `src/infrastructure`
  - [ ] `src/core`
  - [ ] `src/utils`
- [ ] Los módulos que NO deben incluirse están excluidos:
  - [ ] `src/notebooks` (excluido)
  - [ ] `src/pipelines` (excluido)
  - [ ] `src/data` (excluido)
- [ ] `src/__init__.py` exporta correctamente la API pública
- [ ] `__version__` en `src/__init__.py` coincide con `pyproject.toml`

### 1.3 Dependencias

- [ ] Todas las dependencias están especificadas con versiones mínimas
- [ ] Dependencias opcionales están correctamente definidas:
  - [ ] `infer` (spaCy)
  - [ ] `infer-en`, `infer-es`, `infer-all`
  - [ ] `gds` (Graph Data Science)
  - [ ] `ynet` (Visualización)
  - [ ] `dev` (Herramientas de desarrollo)
  - [ ] `experiments` (Opik)
  - [ ] `all` (Todas las extensiones)
- [ ] No hay dependencias duplicadas
- [ ] Las versiones son compatibles entre sí

### 1.4 Documentación

- [ ] README.md está completo y actualizado
- [ ] README.md se renderiza correctamente (Markdown válido)
- [ ] Ejemplos de código en README.md son correctos
- [ ] Links en README.md funcionan
- [ ] Documentación de instalación es clara
- [ ] Documentación de configuración es completa

---

## ✅ Fase 2: Build y Verificación Local

### 2.1 Build del Paquete

- [ ] Ejecutar `uv build` sin errores
- [ ] Se generan ambos archivos en `dist/`:
  - [ ] `ungraph-0.1.0-py3-none-any.whl`
  - [ ] `ungraph-0.1.0.tar.gz`
- [ ] No hay warnings durante el build
- [ ] Tamaño de los archivos es razonable (< 10MB)

### 2.2 Verificación del Wheel

- [ ] Ejecutar `python scripts/verify_wheel.py`
- [ ] Todos los archivos críticos están presentes:
  - [ ] `domain/entities/fact.py`
  - [ ] `domain/entities/entity.py`
  - [ ] `domain/entities/relation.py`
  - [ ] `domain/services/inference_service.py`
  - [ ] `infrastructure/services/spacy_inference_service.py`
  - [ ] `application/use_cases/ingest_document.py`
  - [ ] `application/dependencies.py`
- [ ] Estructura del wheel es correcta

### 2.3 Instalación Local

- [ ] Crear entorno virtual limpio: `python -m venv test_env`
- [ ] Instalar desde wheel: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl`
- [ ] Verificar que `ungraph` se puede importar: `python -c "import ungraph"`
- [ ] Verificar versión: `python -c "import ungraph; print(ungraph.__version__)"`
- [ ] Ejecutar `python scripts/verify_installation.py` - todos los tests pasan

### 2.4 Verificación de Imports

- [ ] `import ungraph` funciona
- [ ] `from ungraph.domain.entities import Fact, Entity, Relation` funciona
- [ ] `from ungraph.domain.services import InferenceService` funciona
- [ ] `from ungraph.application.use_cases import IngestDocumentUseCase` funciona
- [ ] `from ungraph.infrastructure.services import SpacyInferenceService` funciona
- [ ] API pública funciona: `ungraph.configure()`, `ungraph.ingest_document()`, etc.

### 2.5 Dependencias Opcionales

- [ ] Instalar con `infer`: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl[infer]`
- [ ] Verificar que spaCy se instala correctamente
- [ ] Instalar con `gds`: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl[gds]`
- [ ] Verificar que graphdatascience se instala correctamente
- [ ] Instalar con `all`: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl[all]`
- [ ] Verificar que todas las dependencias opcionales se instalan

---

## ✅ Fase 3: Tests y Calidad

### 3.1 Tests Unitarios

- [ ] Ejecutar `pytest tests/ -m unit -v` - todos pasan
- [ ] Cobertura de código es razonable (> 70%)
- [ ] No hay tests que fallen intermitentemente

### 3.2 Tests de Integración (Opcional, requiere Neo4j)

- [ ] Si Neo4j está disponible, ejecutar tests de integración
- [ ] Verificar que los casos de uso funcionan end-to-end

### 3.3 Calidad de Código

- [ ] No hay errores de linting críticos
- [ ] No hay imports no utilizados
- [ ] No hay código muerto

---

## ✅ Fase 4: Publicación en TestPyPI

### 4.1 Preparación para TestPyPI

- [ ] Cambiar nombre del paquete a `ungraphx` en `pyproject.toml`
- [ ] Rebuild: `uv build`
- [ ] Verificar que se generan `ungraphx-0.1.0-*.whl` y `ungraphx-0.1.0.tar.gz`
- [ ] Token de TestPyPI está configurado: `$env:UV_PUBLISH_TOKEN`

### 4.2 Publicación en TestPyPI

- [ ] Publicar: `uv publish --index testpypi --token $env:UV_PUBLISH_TOKEN`
- [ ] Verificar que la publicación fue exitosa
- [ ] Verificar en https://test.pypi.org/project/ungraphx/

### 4.3 Verificación Post-Publicación TestPyPI

- [ ] Crear entorno virtual limpio
- [ ] Instalar desde TestPyPI:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ungraphx==0.1.0
  ```
- [ ] Verificar que `ungraphx` se puede importar
- [ ] Verificar que la funcionalidad básica funciona
- [ ] Verificar que README.md se renderiza correctamente en TestPyPI

### 4.4 Restaurar Nombre Original

- [ ] Cambiar nombre del paquete de vuelta a `ungraph` en `pyproject.toml`
- [ ] Rebuild: `uv build`
- [ ] Verificar que se generan `ungraph-0.1.0-*.whl` y `ungraph-0.1.0.tar.gz`

---

## ✅ Fase 5: Publicación en PyPI Oficial

### 5.1 Preparación Final

- [ ] **CRÍTICO**: Verificar que `pyproject.toml` tiene `name = "ungraph"` (nombre original)
- [ ] Verificar que `ungraph` NO existe en PyPI oficial (ya verificado: ✅ DISPONIBLE)
- [ ] Token de PyPI oficial está configurado: `$env:UV_PUBLISH_TOKEN`
- [ ] Build final: `uv build`
- [ ] Verificar archivos generados: `ungraph-0.1.0-py3-none-any.whl` y `ungraph-0.1.0.tar.gz`

### 5.2 Publicación en PyPI Oficial

- [ ] **ÚLTIMA VERIFICACIÓN**: Revisar checklist completo una vez más
- [ ] Publicar: `uv publish --token $env:UV_PUBLISH_TOKEN`
- [ ] Verificar que la publicación fue exitosa
- [ ] Verificar en https://pypi.org/project/ungraph/

### 5.3 Verificación Post-Publicación PyPI

- [ ] Crear entorno virtual completamente limpio
- [ ] Instalar desde PyPI oficial: `pip install ungraph==0.1.0`
- [ ] Verificar que `ungraph` se puede importar
- [ ] Verificar versión: `python -c "import ungraph; print(ungraph.__version__)"`
- [ ] Ejecutar `python scripts/verify_installation.py` - todos los tests pasan
- [ ] Verificar que la funcionalidad básica funciona:
  - [ ] `ungraph.configure()` funciona
  - [ ] `ungraph.ingest_document()` funciona (si Neo4j está disponible)
  - [ ] `ungraph.search()` funciona (si hay datos)
- [ ] Verificar que README.md se renderiza correctamente en PyPI
- [ ] Verificar que los extras opcionales funcionan: `pip install ungraph[infer]`

---

## ✅ Fase 6: Post-Release

### 6.1 Documentación

- [ ] Actualizar documentación con instrucciones de instalación desde PyPI
- [ ] Actualizar README.md con link a PyPI
- [ ] Crear/actualizar CHANGELOG.md (opcional pero recomendado)

### 6.2 Comunicación

- [ ] Anunciar el release (si aplica)
- [ ] Actualizar repositorio con tag de versión: `git tag v0.1.0`

---

## 🚨 Checklist Crítico (Revisar ANTES de publicar en PyPI oficial)

Antes de ejecutar `uv publish` para PyPI oficial, verificar:

- [ ] ✅ `pyproject.toml` tiene `name = "ungraph"` (NO `ungraphx`)
- [ ] ✅ Versión es `0.1.0`
- [ ] ✅ README.md está completo
- [ ] ✅ LICENSE existe
- [ ] ✅ Build genera archivos con nombre `ungraph-0.1.0-*`
- [ ] ✅ Instalación local funciona correctamente
- [ ] ✅ Todos los imports críticos funcionan
- [ ] ✅ Token de PyPI oficial está configurado (NO token de TestPyPI)
- [ ] ✅ Se probó en TestPyPI primero (como `ungraphx`)

---

## 📝 Notas Importantes

1. **Nunca publicar en PyPI oficial sin probar primero en TestPyPI**
2. **Siempre verificar el nombre del paquete antes de publicar**
3. **Los tokens de TestPyPI y PyPI oficial son diferentes**
4. **Una vez publicado en PyPI oficial, no se puede eliminar, solo crear nuevas versiones**
5. **Verificar que el nombre `ungraph` está disponible antes de publicar**

---

## 🔧 Scripts Útiles

### Cambiar nombre para TestPyPI
```bash
# Usar script helper (ver scripts/publish_helper.py)
python scripts/publish_helper.py --name ungraphx
uv build
```

### Restaurar nombre para PyPI oficial
```bash
python scripts/publish_helper.py --name ungraph
uv build
```

### Verificar antes de publicar
```bash
# Verificar configuración
python -c "import tomli; data = tomli.load(open('pyproject.toml', 'rb')); print(f\"Name: {data['project']['name']}\")"

# Verificar build
uv build
ls dist/

# Verificar instalación
uv pip install dist/ungraph-0.1.0-py3-none-any.whl
python scripts/verify_installation.py
```

