#!/usr/bin/env python
"""
Script helper para cambiar el nombre del paquete entre 'ungraph' y 'ungraphx'
para publicar en TestPyPI (ungraphx) y PyPI oficial (ungraph).
"""

import sys
import re
from pathlib import Path
from typing import Literal

def update_pyproject_name(name: str) -> bool:
    """Actualiza el nombre del paquete en pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"[ERROR] pyproject.toml no encontrado: {pyproject_path}")
        return False
    
    content = pyproject_path.read_text(encoding='utf-8')
    
    # Buscar y reemplazar el nombre del paquete
    pattern = r'^name\s*=\s*["\']([^"\']+)["\']'
    replacement = f'name = "{name}"'
    
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if new_content == content:
        print(f"[WARNING] No se encontró 'name = ...' en pyproject.toml")
        return False
    
    # También actualizar referencias en optional-dependencies
    if name == "ungraphx":
        # Cambiar referencias de ungraph[xxx] a ungraphx[xxx]
        new_content = new_content.replace('"ungraph[', '"ungraphx[')
    else:
        # Cambiar referencias de ungraphx[xxx] a ungraph[xxx]
        new_content = new_content.replace('"ungraphx[', '"ungraph[')
    
    pyproject_path.write_text(new_content, encoding='utf-8')
    print(f"[OK] pyproject.toml actualizado: name = '{name}'")
    
    # Verificar que el cambio se aplicó
    if f'name = "{name}"' in new_content:
        print(f"[OK] Verificación: nombre actualizado correctamente a '{name}'")
        return True
    else:
        print(f"[ERROR] Verificación falló: nombre no se actualizó correctamente")
        return False

def update_src_init_version(name: str) -> bool:
    """Actualiza referencias al nombre del paquete en src/__init__.py si es necesario."""
    # Por ahora no necesitamos cambiar nada en src/__init__.py
    # porque el nombre del paquete instalado no afecta los imports internos
    return True

def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python publish_helper.py --name <ungraph|ungraphx>")
        print("\nEjemplos:")
        print("  python publish_helper.py --name ungraphx  # Para TestPyPI")
        print("  python publish_helper.py --name ungraph   # Para PyPI oficial")
        sys.exit(1)
    
    if sys.argv[1] != "--name":
        print(f"[ERROR] Opción desconocida: {sys.argv[1]}")
        print("Uso: python publish_helper.py --name <ungraph|ungraphx>")
        sys.exit(1)
    
    if len(sys.argv) < 3:
        print("[ERROR] Falta especificar el nombre del paquete")
        print("Uso: python publish_helper.py --name <ungraph|ungraphx>")
        sys.exit(1)
    
    new_name = sys.argv[2]
    
    if new_name not in ["ungraph", "ungraphx"]:
        print(f"[ERROR] Nombre inválido: {new_name}")
        print("Debe ser 'ungraph' o 'ungraphx'")
        sys.exit(1)
    
    print("=" * 60)
    print(f"ACTUALIZANDO NOMBRE DEL PAQUETE A: {new_name}")
    print("=" * 60)
    
    success = True
    
    # Actualizar pyproject.toml
    if not update_pyproject_name(new_name):
        success = False
    
    # Actualizar src/__init__.py si es necesario
    if not update_src_init_version(new_name):
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print(f"[SUCCESS] Nombre del paquete actualizado a '{new_name}'")
        print("\nPróximos pasos:")
        print("  1. Ejecutar: uv build")
        print(f"  2. Verificar que se generan archivos con nombre '{new_name}-0.1.0-*'")
        if new_name == "ungraphx":
            print("  3. Publicar en TestPyPI: uv publish --index testpypi --token $env:UV_PUBLISH_TOKEN")
        else:
            print("  3. Publicar en PyPI oficial: uv publish --token $env:UV_PUBLISH_TOKEN")
    else:
        print("[ERROR] Hubo problemas al actualizar el nombre del paquete")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

