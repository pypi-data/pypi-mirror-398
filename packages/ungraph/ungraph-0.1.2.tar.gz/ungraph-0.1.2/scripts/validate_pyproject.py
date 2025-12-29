#!/usr/bin/env python
"""
Script para validar la configuración de pyproject.toml antes de publicar.
"""

import sys
from pathlib import Path

try:
    import tomli
except ImportError:
    print("[ERROR] tomli no está instalado. Instalar con: pip install tomli")
    sys.exit(1)

def validate_pyproject():
    """Valida la configuración de pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"[ERROR] pyproject.toml no encontrado: {pyproject_path}")
        return False
    
    with open(pyproject_path, 'rb') as f:
        data = tomli.load(f)
    
    errors = []
    warnings = []
    
    print("=" * 60)
    print("VALIDACION DE pyproject.toml")
    print("=" * 60)
    
    # Validar nombre del paquete
    project_name = data.get('project', {}).get('name', '')
    print(f"\n[1] Nombre del paquete: {project_name}")
    if project_name == "ungraph":
        print("  ✅ Correcto: 'ungraph' (para PyPI oficial)")
    elif project_name == "ungraphx":
        print("  ⚠️  ADVERTENCIA: 'ungraphx' (solo para TestPyPI)")
        warnings.append("Nombre del paquete es 'ungraphx' - recordar cambiar a 'ungraph' para PyPI oficial")
    else:
        errors.append(f"Nombre del paquete inválido: {project_name}")
        print(f"  ❌ ERROR: Nombre debe ser 'ungraph' o 'ungraphx'")
    
    # Validar versión
    version = data.get('project', {}).get('version', '')
    print(f"\n[2] Versión: {version}")
    if version == "0.1.0":
        print("  ✅ Correcto")
    else:
        warnings.append(f"Versión es {version}, esperada 0.1.0")
        print(f"  ⚠️  ADVERTENCIA: Versión es {version}")
    
    # Validar índices
    print(f"\n[3] Configuración de índices:")
    indices = data.get('tool', {}).get('uv', {}).get('index', [])
    
    testpypi_found = False
    pypi_found = False
    
    for idx in indices:
        idx_name = idx.get('name', '')
        idx_url = idx.get('url', '')
        is_default = idx.get('default', False)
        
        print(f"  - Índice: '{idx_name}' -> {idx_url} (default: {is_default})")
        
        if idx_name == "testpypi":
            testpypi_found = True
            if idx_url == "https://test.pypi.org/simple":
                print("    ✅ URL correcta para TestPyPI")
            else:
                errors.append(f"URL incorrecta para testpypi: {idx_url}")
        elif idx_name == "pypi":
            pypi_found = True
            if idx_url == "https://pypi.org/simple":
                print("    ✅ URL correcta para PyPI")
            else:
                errors.append(f"URL incorrecta para pypi: {idx_url}")
        else:
            errors.append(f"Nombre de índice inválido: {idx_name} (debe ser 'testpypi' o 'pypi')")
    
    if not testpypi_found:
        warnings.append("Índice 'testpypi' no encontrado")
    if not pypi_found:
        errors.append("Índice 'pypi' no encontrado")
    
    # Validar build system
    print(f"\n[4] Build system:")
    build_system = data.get('build-system', {})
    build_backend = build_system.get('build-backend', '')
    if build_backend == "hatchling.build":
        print("  ✅ hatchling.build configurado correctamente")
    else:
        errors.append(f"Build backend incorrecto: {build_backend}")
    
    # Validar paquetes incluidos
    print(f"\n[5] Paquetes incluidos en wheel:")
    wheel_packages = data.get('tool', {}).get('hatch', {}).get('build', {}).get('targets', {}).get('wheel', {}).get('packages', [])
    required_packages = ['src/domain', 'src/application', 'src/infrastructure', 'src/core', 'src/utils']
    
    for pkg in required_packages:
        if pkg in wheel_packages:
            print(f"  ✅ {pkg}")
        else:
            errors.append(f"Paquete faltante en wheel: {pkg}")
            print(f"  ❌ {pkg} (FALTANTE)")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERRORES ENCONTRADOS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✅ TODAS LAS VALIDACIONES PASARON")
        print("\nEl proyecto está listo para:")
        if project_name == "ungraph":
            print("  - Publicar en PyPI oficial")
        else:
            print("  - Publicar en TestPyPI (recordar cambiar nombre a 'ungraph' para PyPI oficial)")
    
    print("=" * 60)
    
    return len(errors) == 0

if __name__ == "__main__":
    success = validate_pyproject()
    sys.exit(0 if success else 1)

