#!/usr/bin/env python
"""
Script unificado para build y publicación de ungraph.

Variables de entorno:
    UNGRAPH_RELEASE: Token de TestPyPI
    UNGRAPH_RELEASE_PROD: Token de PyPI oficial

Uso:
    python scripts/publish.py build                    # Solo build
    python scripts/publish.py publish --test            # Publicar en TestPyPI
    python scripts/publish.py publish --prod           # Publicar en PyPI oficial
    python scripts/publish.py validate                 # Validar configuración
"""

import sys
import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Literal

# Cargar variables de entorno desde .env (debe ser lo primero)
try:
    from dotenv import load_dotenv, find_dotenv
    # Intentar encontrar .env automáticamente
    env_path = find_dotenv()
    if not env_path:
        # Si no se encuentra, buscar en la raíz del proyecto
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            env_path = str(env_file)
    
    if env_path:
        load_dotenv(env_path, override=False)  # override=False: no sobrescribir variables del sistema
        # Solo mostrar si estamos en modo verbose o si hay variables relevantes
        if os.environ.get('UNGRAPH_RELEASE') or os.environ.get('UNGRAPH_RELEASE_PROD'):
            print(f"[INFO] Variables de entorno cargadas desde: {env_path}")
except ImportError:
    pass  # python-dotenv no es crítico, usar variables del sistema

# Colores para output (sin emojis para compatibilidad Windows)
class Colors:
    OK = "[OK]"
    ERROR = "[ERROR]"
    WARNING = "[WARNING]"
    INFO = "[INFO]"

def get_project_root() -> Path:
    """Obtiene la raíz del proyecto."""
    return Path(__file__).parent.parent

def read_pyproject() -> dict:
    """Lee y parsea pyproject.toml."""
    pyproject_path = get_project_root() / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"{Colors.ERROR} pyproject.toml no encontrado")
        sys.exit(1)
    
    content = pyproject_path.read_text(encoding='utf-8')
    
    # Extraer nombre del paquete
    name_match = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    name = name_match.group(1) if name_match else None
    
    # Extraer versión
    version_match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    version = version_match.group(1) if version_match else None
    
    return {
        'name': name,
        'version': version,
        'content': content,
        'path': pyproject_path
    }

def update_package_name(name: str) -> bool:
    """Actualiza el nombre del paquete en pyproject.toml.
    
    Solo cambia:
    - El nombre del paquete en [project]
    - Las referencias en [project.optional-dependencies]
    
    NO cambia los nombres de los índices (siempre "testpypi" y "pypi").
    """
    pyproject = read_pyproject()
    content = pyproject['content']
    
    # 1. Cambiar nombre del paquete usando regex (solo en [project])
    pattern = r'^name\s*=\s*["\'](ungraphx?|ungraph)["\']'
    replacement = f'name = "{name}"'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 2. Cambiar referencias en optional-dependencies
    if name == "ungraphx":
        new_content = new_content.replace('"ungraph[', '"ungraphx[')
    else:
        new_content = new_content.replace('"ungraphx[', '"ungraph[')
    
    # 3. Asegurar que los índices siempre sean correctos (nunca cambiar)
    lines = new_content.split('\n')
    result_lines = []
    index_num = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('[[tool.uv.index]]'):
            index_num += 1
            result_lines.append(line)
        elif 'name =' in line and i > 0 and lines[i-1].strip().startswith('[[tool.uv.index]]'):
            # Es la línea del nombre del índice (justo después de [[tool.uv.index]])
            if index_num == 1:
                result_lines.append('name = "testpypi"')
            else:
                result_lines.append('name = "pypi"')
        else:
            result_lines.append(line)
    
    new_content = '\n'.join(result_lines)
    pyproject['path'].write_text(new_content, encoding='utf-8')
    
    # Verificar que el nombre del paquete se cambió
    if f'name = "{name}"' in new_content:
        print(f"{Colors.OK} Nombre del paquete actualizado a: {name}")
        return True
    else:
        print(f"{Colors.ERROR} Error al actualizar nombre del paquete")
        print(f"{Colors.INFO} Contenido actual: {read_pyproject()['name']}")
        return False

def validate_configuration(target: Literal["test", "prod"] = "prod") -> bool:
    """Valida la configuración antes de publicar."""
    print("=" * 60)
    print("VALIDACION DE CONFIGURACION")
    print("=" * 60)
    
    # Mostrar variables de entorno disponibles (solo prefijos, no valores completos)
    test_token = os.environ.get('UNGRAPH_RELEASE')
    prod_token = os.environ.get('UNGRAPH_RELEASE_PROD')
    if test_token:
        print(f"[INFO] UNGRAPH_RELEASE configurado ({len(test_token)} caracteres)")
    if prod_token:
        print(f"[INFO] UNGRAPH_RELEASE_PROD configurado ({len(prod_token)} caracteres)")
    
    pyproject = read_pyproject()
    name = pyproject['name']
    version = pyproject['version']
    
    errors = []
    warnings = []
    
    # Validar nombre según target
    if target == "test":
        if name != "ungraphx":
            errors.append(f"Para TestPyPI el nombre debe ser 'ungraphx', actual: '{name}'")
            print(f"{Colors.ERROR} Nombre incorrecto para TestPyPI: {name}")
        else:
            print(f"{Colors.OK} Nombre correcto para TestPyPI: {name}")
    else:  # prod
        if name != "ungraph":
            errors.append(f"Para PyPI oficial el nombre debe ser 'ungraph', actual: '{name}'")
            print(f"{Colors.ERROR} Nombre incorrecto para PyPI oficial: {name}")
        else:
            print(f"{Colors.OK} Nombre correcto para PyPI oficial: {name}")
    
    # Validar versión
    if version:
        print(f"{Colors.OK} Version: {version}")
    else:
        errors.append("No se pudo determinar la versión")
    
    # Validar archivos de distribución
    dist_path = get_project_root() / "dist"
    if target == "test":
        expected_files = [
            f"ungraphx-{version}-py3-none-any.whl",
            f"ungraphx-{version}.tar.gz"
        ]
    else:
        expected_files = [
            f"ungraph-{version}-py3-none-any.whl",
            f"ungraph-{version}.tar.gz"
        ]
    
    missing_files = []
    for filename in expected_files:
        filepath = dist_path / filename
        if filepath.exists():
            print(f"{Colors.OK} Archivo encontrado: {filename}")
        else:
            missing_files.append(filename)
            errors.append(f"Archivo faltante: {filename}")
            print(f"{Colors.ERROR} Archivo faltante: {filename}")
    
    # Validar token
    if target == "test":
        token = os.environ.get('UNGRAPH_RELEASE') or os.environ.get('UV_PUBLISH_TOKEN')
        token_name = "UNGRAPH_RELEASE o UV_PUBLISH_TOKEN"
    else:
        token = os.environ.get('UNGRAPH_RELEASE_PROD') or os.environ.get('UV_PUBLISH_TOKEN')
        token_name = "UNGRAPH_RELEASE_PROD o UV_PUBLISH_TOKEN"
    
    if not token:
        errors.append(f"Token no configurado: {token_name}")
        print(f"{Colors.ERROR} Token no configurado: {token_name}")
    else:
        print(f"{Colors.OK} Token configurado ({len(token)} caracteres)")
    
    # Resumen
    print("\n" + "=" * 60)
    if errors:
        print(f"{Colors.ERROR} ERRORES ENCONTRADOS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"{Colors.OK} TODAS LAS VALIDACIONES PASARON")
        return True

def run_build() -> bool:
    """Ejecuta uv build, limpiando dist/ primero."""
    print("=" * 60)
    print("BUILD DEL PAQUETE")
    print("=" * 60)
    
    project_root = get_project_root()
    dist_path = project_root / "dist"
    
    # Limpiar dist/ antes de build
    if dist_path.exists():
        import shutil
        for file in dist_path.glob("*"):
            if file.is_file() and file.name != ".gitignore":
                file.unlink()
        print(f"{Colors.INFO} Directorio dist/ limpiado")
    
    result = subprocess.run(
        ["uv", "build"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"{Colors.OK} Build exitoso")
        print(result.stdout)
        return True
    else:
        print(f"{Colors.ERROR} Build fallido")
        print(result.stderr)
        return False

def publish(target: Literal["test", "prod"]) -> bool:
    """Publica el paquete en TestPyPI o PyPI oficial."""
    print("=" * 60)
    print(f"PUBLICACION EN {'TestPyPI' if target == 'test' else 'PyPI OFICIAL'}")
    print("=" * 60)
    
    # Validar antes de publicar
    if not validate_configuration(target):
        print(f"\n{Colors.ERROR} Validacion fallida. No se puede publicar.")
        return False
    
    # Obtener token
    if target == "test":
        token = os.environ.get('UNGRAPH_RELEASE') or os.environ.get('UV_PUBLISH_TOKEN')
        if not token:
            print(f"{Colors.ERROR} Token no configurado: UNGRAPH_RELEASE o UV_PUBLISH_TOKEN")
            return False
        index = "testpypi"
    else:
        token = os.environ.get('UNGRAPH_RELEASE_PROD') or os.environ.get('UV_PUBLISH_TOKEN')
        if not token:
            print(f"{Colors.ERROR} Token no configurado: UNGRAPH_RELEASE_PROD o UV_PUBLISH_TOKEN")
            return False
        index = None  # PyPI oficial es el default
    
    # Construir comando
    cmd = ["uv", "publish", "--token", token]
    if index:
        cmd.extend(["--index", index])
    
    print(f"\n{Colors.INFO} Ejecutando: {' '.join(cmd[:3])} --token *** --index {index if index else 'pypi'}")
    
    project_root = get_project_root()
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"\n{Colors.OK} Publicacion exitosa")
        print(result.stdout)
        if target == "test":
            print(f"\n{Colors.INFO} Verificar en: https://test.pypi.org/project/ungraphx/")
        else:
            print(f"\n{Colors.INFO} Verificar en: https://pypi.org/project/ungraph/")
        return True
    else:
        print(f"\n{Colors.ERROR} Publicacion fallida")
        print(result.stderr)
        return False

def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "build":
        success = run_build()
        sys.exit(0 if success else 1)
    
    elif command == "publish":
        if len(sys.argv) < 3:
            print(f"{Colors.ERROR} Especifica --test o --prod")
            print("  python scripts/publish.py publish --test   # TestPyPI (ungraphx)")
            print("  python scripts/publish.py publish --prod    # PyPI oficial (ungraph)")
            sys.exit(1)
        
        target_arg = sys.argv[2]
        if target_arg == "--test":
            # Cambiar nombre a ungraphx para TestPyPI
            print(f"{Colors.INFO} Configurando para TestPyPI (nombre: ungraphx)...")
            if not update_package_name("ungraphx"):
                sys.exit(1)
            if not run_build():
                sys.exit(1)
            success = publish("test")
            # Restaurar nombre a ungraph después de publicar
            print(f"\n{Colors.INFO} Restaurando nombre a 'ungraph'...")
            update_package_name("ungraph")
        elif target_arg == "--prod":
            # Asegurar nombre es ungraph para PyPI oficial
            print(f"{Colors.INFO} Configurando para PyPI oficial (nombre: ungraph)...")
            if not update_package_name("ungraph"):
                sys.exit(1)
            if not run_build():
                sys.exit(1)
            success = publish("prod")
        else:
            print(f"{Colors.ERROR} Opcion invalida: {target_arg}")
            print("  Usa --test o --prod")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
    
    elif command == "validate":
        target = "prod"
        if len(sys.argv) >= 3 and sys.argv[2] == "--test":
            target = "test"
        validate_configuration(target)
        sys.exit(0)
    
    else:
        print(f"{Colors.ERROR} Comando desconocido: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()

