# Pre-Build Checklist

Este documento resume las validaciones realizadas antes del build y publish del paquete.

## ✅ Correcciones Realizadas

### 1. Imports Absolutos Corregidos
- ✅ Todos los imports de `from domain...`, `from application...`, `from infrastructure...` fueron cambiados a `from ungraph.domain...`, etc.
- ✅ Eliminados fallbacks de imports en `__init__.py`
- ✅ Archivos corregidos: ~20 archivos en total

### 2. API Público Alineado con README
- ✅ Función `vector_search()` agregada al API público
- ✅ Referencias a `search_by_entity()` eliminadas del README (no existe)
- ✅ Parámetro `extract_entities` eliminado de ejemplos en README

### 3. Descripción en pyproject.toml
- ✅ Cambiada de "Graph Query Language Standard" a descripción más precisa
- ✅ Ahora dice: "Python framework for building Knowledge Graphs from unstructured text using Neo4j (Cypher), aligned with property-graph standards"

### 4. Claims de "Production-Ready"
- ✅ Agregadas notas en README indicando estado alpha
- ✅ Mantiene arquitectura pero aclara que API puede cambiar

## ✅ Validaciones Creadas

### 1. Smoke Test de Instalación
- ✅ Script: `scripts/smoke_test_installation.py`
- ✅ Valida: imports, API público, funcionalidad básica
- ✅ Uso: `python scripts/smoke_test_installation.py` (después de `pip install .`)

### 2. Test de Instalación para CI/CD
- ✅ Archivo: `tests/test_installation.py`
- ✅ 6 tests que validan: imports, API público, clases, configuración
- ✅ Ejecución: `pytest tests/test_installation.py -v`
- ✅ Estado: ✅ TODOS LOS TESTS PASAN

### 3. Validación de Links de Documentación
- ✅ Script: `scripts/validate_docs_links.py`
- ✅ Valida que todos los links en README.md existan
- ✅ Estado: ✅ TODOS LOS LINKS SON VÁLIDOS (5/5)

### 4. CI/CD Workflow Actualizado
- ✅ Archivo: `.github/workflows/ci.yml`
- ✅ Agregado job `installation-test` que:
  - Construye el paquete (`python -m build`)
  - Instala desde wheel (`pip install dist/*.whl`)
  - Ejecuta smoke test
  - Ejecuta tests de instalación

## 📋 Checklist Pre-Build

Antes de ejecutar `uv build` y `uv publish`, verificar:

- [x] Todos los imports absolutos corregidos
- [x] API público alineado con README
- [x] Descripción en pyproject.toml corregida
- [x] Claims de production-ready ajustados
- [x] Smoke test creado y funcional
- [x] Tests de instalación creados y pasando
- [x] Links de documentación validados
- [x] CI/CD workflow actualizado para usar `uv`
- [x] Script de validación pre-build creado

## ✅ Validación Automática

Ejecutar el script de validación pre-build que ejecuta todas las verificaciones:

```bash
python scripts/pre_build_validation.py
```

Este script valida:
1. ✅ Links de documentación (5/5 válidos)
2. ✅ Tests de instalación (6/6 pasando)
3. ⚠️ Smoke test (requiere paquete instalado)
4. ✅ Configuración de publicación (tokens y archivos)

## 🚀 Próximos Pasos (usando uv y scripts propios)

1. **Verificar configuración:**
   ```bash
   python scripts/check_publish_status.py
   ```

2. **Build del paquete:**
   ```bash
   python scripts/publish.py build
   ```
   O directamente:
   ```bash
   uv build
   ```

3. **Verificar wheel:**
   ```bash
   python scripts/verify_wheel.py
   ```

4. **Smoke test desde wheel:**
   ```bash
   uv pip install dist/ungraph-*.whl
   python scripts/smoke_test_installation.py
   ```

5. **Validar configuración antes de publicar:**
   ```bash
   python scripts/publish.py validate --test   # Para TestPyPI
   python scripts/publish.py validate          # Para PyPI oficial
   ```

6. **Publicar a TestPyPI (recomendado primero):**
   ```bash
   # Configurar token de TestPyPI
   $env:UV_PUBLISH_TOKEN="pypi-tu-token-de-testpypi"
   # O usar variable específica:
   $env:UNGRAPH_RELEASE="pypi-tu-token-de-testpypi"
   
   # Publicar (el script maneja automáticamente el cambio de nombre a ungraphx)
   python scripts/publish.py publish --test
   ```

7. **Probar instalación desde TestPyPI:**
   ```bash
   uv pip install --index-url https://test.pypi.org/simple/ ungraphx
   python scripts/smoke_test_installation.py
   ```

8. **Publicar a PyPI oficial (solo si TestPyPI funciona):**
   ```bash
   # Configurar token de PyPI oficial
   $env:UV_PUBLISH_TOKEN="pypi-tu-token-de-pypi"
   # O usar variable específica:
   $env:UNGRAPH_RELEASE_PROD="pypi-tu-token-de-pypi"
   
   # Publicar (el script asegura que el nombre sea ungraph)
   python scripts/publish.py publish --prod
   ```

## 📝 Notas Importantes

- El paquete está en estado **alpha** según `pyproject.toml`
- La API puede cambiar en versiones futuras
- Los tests de instalación NO requieren Neo4j (solo validan imports y estructura)
- Los tests de integración/E2E requieren Neo4j y se ejecutan en CI/CD separadamente

