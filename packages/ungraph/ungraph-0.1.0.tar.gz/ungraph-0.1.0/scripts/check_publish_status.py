#!/usr/bin/env python
"""
Script para verificar el estado de publicación y configuración de tokens.
"""

import sys
import os
from pathlib import Path

def check_configuration():
    """Verifica la configuración para publicación."""
    print("=" * 60)
    print("VERIFICACION DE CONFIGURACION PARA PUBLICACION")
    print("=" * 60)
    
    # Verificar pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding='utf-8')
        
        # Verificar nombre del paquete
        if 'name = "ungraph"' in content:
            print("\n[OK] Nombre del paquete: ungraph (correcto para PyPI oficial)")
        elif 'name = "ungraphx"' in content:
            print("\n[WARNING] Nombre del paquete: ungraphx (solo para TestPyPI)")
            print("   ADVERTENCIA: Cambiar a 'ungraph' para PyPI oficial")
        else:
            print("\n[ERROR] No se pudo determinar el nombre del paquete")
        
        # Verificar índices
        if 'name = "testpypi"' in content:
            print("[OK] Indice TestPyPI configurado correctamente")
        else:
            print("[WARNING] Indice TestPyPI no encontrado o mal configurado")
        
        if 'name = "pypi"' in content:
            print("[OK] Indice PyPI configurado correctamente")
        else:
            print("[WARNING] Indice PyPI no encontrado o mal configurado")
    
    # Verificar token
    print("\n" + "=" * 60)
    print("VERIFICACION DE TOKEN")
    print("=" * 60)
    
    token = os.environ.get('UV_PUBLISH_TOKEN', '')
    
    if not token:
        print("\n[ERROR] UV_PUBLISH_TOKEN no esta configurado")
        print("\nPara configurar el token:")
        print("  PowerShell: $env:UV_PUBLISH_TOKEN=\"pypi-tu-token-aqui\"")
        print("  Bash: export UV_PUBLISH_TOKEN=\"pypi-tu-token-aqui\"")
    else:
        print(f"\n[OK] UV_PUBLISH_TOKEN esta configurado")
        print(f"   Longitud: {len(token)} caracteres")
        print(f"   Prefijo: {token[:10]}...")
        
        # Intentar determinar si es token de TestPyPI o PyPI oficial
        # Los tokens de TestPyPI suelen tener "test.pypi.org" en el payload base64
        # Los tokens de PyPI oficial tienen "pypi.org"
        if "test" in token.lower() or len(token) < 50:
            print("   [WARNING] Este token parece ser de TestPyPI")
            print("   [WARNING] Para PyPI oficial necesitas un token diferente")
        else:
            print("   [INFO] Token parece ser de PyPI oficial")
    
    # Verificar archivos de distribución
    print("\n" + "=" * 60)
    print("VERIFICACION DE ARCHIVOS DE DISTRIBUCION")
    print("=" * 60)
    
    dist_path = Path(__file__).parent.parent / "dist"
    if dist_path.exists():
        files = list(dist_path.glob("ungraph-*.whl")) + list(dist_path.glob("ungraph-*.tar.gz"))
        if files:
            print(f"\n[OK] Archivos encontrados en dist/:")
            for f in files:
                print(f"   - {f.name}")
        else:
            print("\n[WARNING] No se encontraron archivos de distribucion")
            print("   Ejecutar: uv build")
    else:
        print("\n[WARNING] Directorio dist/ no existe")
        print("   Ejecutar: uv build")
    
    # Instrucciones
    print("\n" + "=" * 60)
    print("INSTRUCCIONES PARA PUBLICAR")
    print("=" * 60)
    
    print("\n1. Para TestPyPI:")
    print("   python scripts/publish_helper.py --name ungraphx")
    print("   uv build")
    print("   $env:UV_PUBLISH_TOKEN=\"token-de-testpypi\"")
    print("   uv publish --index testpypi --token $env:UV_PUBLISH_TOKEN")
    
    print("\n2. Para PyPI Oficial:")
    print("   python scripts/publish_helper.py --name ungraph")
    print("   uv build")
    print("   $env:UV_PUBLISH_TOKEN=\"token-de-pypi-oficial\"")
    print("   uv publish --token $env:UV_PUBLISH_TOKEN")
    
    print("\n" + "=" * 60)
    print("NOTAS IMPORTANTES")
    print("=" * 60)
    print("\n[IMPORTANTE] Los tokens de TestPyPI y PyPI oficial son DIFERENTES")
    print("[IMPORTANTE] Necesitas generar un token en https://pypi.org/manage/account/#api-tokens")
    print("[IMPORTANTE] El token debe tener scope 'Entire account' o al menos 'Upload packages'")
    print("[IMPORTANTE] El formato del token debe ser: pypi-xxxxxxxxxxxxx")

if __name__ == "__main__":
    check_configuration()

