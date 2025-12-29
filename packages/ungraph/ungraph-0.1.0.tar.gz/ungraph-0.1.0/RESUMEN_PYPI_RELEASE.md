# Resumen Ejecutivo: Checklist para PyPI Oficial

## 🎯 Objetivo
Publicar `ungraph v0.1.0` en PyPI oficial con el nombre `ungraph`.

## 📌 Estrategia de Nombres

- **TestPyPI**: `ungraphx` (porque `ungraph` ya existe en TestPyPI)
- **PyPI Oficial**: `ungraph` (nombre disponible ✅)

## ⚠️ Validaciones Críticas ANTES de Publicar en PyPI Oficial

### 1. Configuración del Proyecto (CRÍTICO)

```bash
# Verificar que el nombre es "ungraph" (NO "ungraphx")
python -c "import tomli; data = tomli.load(open('pyproject.toml', 'rb')); print(f\"Name: {data['project']['name']}\")"
```

**Debe mostrar**: `Name: ungraph`

### 2. Build y Verificación

```bash
# 1. Build
uv build

# 2. Verificar archivos generados
ls dist/
# Debe mostrar: ungraph-0.1.0-py3-none-any.whl y ungraph-0.1.0.tar.gz

# 3. Verificar contenido del wheel
python scripts/verify_wheel.py

# 4. Instalación local
uv pip install dist/ungraph-0.1.0-py3-none-any.whl

# 5. Verificar instalación
python scripts/verify_installation.py
```

### 3. Verificación de Imports Críticos

```python
# Ejecutar en Python
import ungraph
print(ungraph.__version__)  # Debe ser "0.1.0"

from ungraph.domain.entities import Fact, Entity, Relation
from ungraph.application.use_cases import IngestDocumentUseCase
from ungraph.infrastructure.services import SpacyInferenceService

# API pública
ungraph.configure(neo4j_uri="bolt://localhost:7687", neo4j_password="test")
```

### 4. Archivos Requeridos

- [ ] `pyproject.toml` con `name = "ungraph"` ✅
- [ ] `README.md` completo y actualizado
- [ ] `LICENSE` presente (MIT)
- [ ] Versión `0.1.0` en `pyproject.toml` y `src/__init__.py`

## 🚀 Proceso de Publicación

### Paso 1: Publicar en TestPyPI (como `ungraphx`)

```bash
# 1. Cambiar nombre a ungraphx
python scripts/publish_helper.py --name ungraphx

# 2. Build
uv build

# 3. Verificar archivos: ungraphx-0.1.0-*
ls dist/

# 4. Publicar en TestPyPI
$env:UV_PUBLISH_TOKEN="pypi-AgENdGVzdC5weXBpLm9yZwIkZjZlNTM0NmEtYmY3Zi00ZTkwLWJkOGUtNjQ3ZDVjMzY5MDExAAIqWzMsIjljZmFlNTE2LTc3NzMtNDRkNS04N2UxLWU4NjhhMzRhNDYyNyJdAAAGIDzCVuzjvwTxHP1BMb2RD1POYs4IiYzKnXb3glI3kwR7"
uv publish --index testpypi --token $env:UV_PUBLISH_TOKEN

# 5. Verificar en https://test.pypi.org/project/ungraphx/
```

### Paso 2: Restaurar Nombre y Publicar en PyPI Oficial

```bash
# 1. CRÍTICO: Restaurar nombre a "ungraph"
python scripts/publish_helper.py --name ungraph

# 2. Verificar que el nombre es correcto
python -c "import tomli; data = tomli.load(open('pyproject.toml', 'rb')); assert data['project']['name'] == 'ungraph', 'ERROR: Nombre incorrecto!'; print('OK: Nombre es ungraph')"

# 3. Build final
uv build

# 4. Verificar archivos: ungraph-0.1.0-* (NO ungraphx)
ls dist/

# 5. ÚLTIMA VERIFICACIÓN: Revisar checklist completo
# Ver CHECKLIST_PYPI_RELEASE.md

# 6. Publicar en PyPI oficial (necesita token de PyPI oficial, NO TestPyPI)
$env:UV_PUBLISH_TOKEN="pypi-token-pypi-oficial"
uv publish --token $env:UV_PUBLISH_TOKEN

# 7. Verificar en https://pypi.org/project/ungraph/
```

## 🔍 Checklist Rápido Pre-Publicación PyPI

Antes de ejecutar `uv publish` para PyPI oficial, verificar:

- [ ] ✅ `pyproject.toml` tiene `name = "ungraph"` (NO `ungraphx`)
- [ ] ✅ Versión es `0.1.0`
- [ ] ✅ Build genera `ungraph-0.1.0-*.whl` y `ungraph-0.1.0.tar.gz`
- [ ] ✅ Instalación local funciona: `uv pip install dist/ungraph-0.1.0-py3-none-any.whl`
- [ ] ✅ `python scripts/verify_installation.py` pasa todos los tests
- [ ] ✅ Token es de PyPI oficial (NO de TestPyPI)
- [ ] ✅ Se probó primero en TestPyPI como `ungraphx`

## 📝 Notas Importantes

1. **NUNCA publicar en PyPI oficial sin probar primero en TestPyPI**
2. **Siempre verificar el nombre del paquete antes de publicar**
3. **Los tokens de TestPyPI y PyPI oficial son diferentes**
4. **Una vez publicado en PyPI oficial, no se puede eliminar, solo crear nuevas versiones**
5. **El nombre `ungraph` está disponible en PyPI oficial** ✅

## 🛠️ Scripts Útiles

### Cambiar nombre para TestPyPI
```bash
python scripts/publish_helper.py --name ungraphx
uv build
```

### Restaurar nombre para PyPI oficial
```bash
python scripts/publish_helper.py --name ungraph
uv build
```

### Verificar configuración
```bash
python -c "import tomli; data = tomli.load(open('pyproject.toml', 'rb')); print(f\"Name: {data['project']['name']}, Version: {data['project']['version']}\")"
```

## 📚 Documentación Completa

Para el checklist completo y detallado, ver: `CHECKLIST_PYPI_RELEASE.md`

