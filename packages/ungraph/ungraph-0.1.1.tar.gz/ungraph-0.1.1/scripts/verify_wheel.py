#!/usr/bin/env python
"""Script para verificar el contenido del wheel generado."""

import zipfile
from pathlib import Path

wheel_path = Path(__file__).parent.parent / "dist" / "ungraph-0.1.0-py3-none-any.whl"

if not wheel_path.exists():
    print(f"[ERROR] Wheel no encontrado: {wheel_path}")
    exit(1)

with zipfile.ZipFile(wheel_path) as whl:
    all_files = whl.namelist()
    
    # Filtrar solo archivos Python relevantes
    python_files = [f for f in all_files if f.endswith('.py')]
    domain_files = [f for f in python_files if f.startswith('domain/')]
    infra_files = [f for f in python_files if f.startswith('infrastructure/')]
    app_files = [f for f in python_files if f.startswith('application/')]
    
    # Verificar archivos críticos
    critical_files = [
        'domain/entities/fact.py',
        'domain/entities/entity.py',
        'domain/entities/relation.py',
        'domain/services/inference_service.py',
        'infrastructure/services/spacy_inference_service.py',
        'application/use_cases/ingest_document.py',
        'application/dependencies.py',
    ]
    
    print("=" * 60)
    print("VERIFICACION DEL WHEEL")
    print("=" * 60)
    print(f"\n[OK] Total archivos en wheel: {len(all_files)}")
    print(f"[OK] Archivos Python: {len(python_files)}")
    print(f"[OK] Archivos domain/: {len(domain_files)}")
    print(f"[OK] Archivos infrastructure/: {len(infra_files)}")
    print(f"[OK] Archivos application/: {len(app_files)}")
    
    print("\n" + "=" * 60)
    print("VERIFICACION DE ARCHIVOS CRITICOS")
    print("=" * 60)
    
    all_critical_present = True
    for file_path in critical_files:
        # Buscar en todos los archivos (puede tener prefijo como ungraph-0.1.0.data/purelib/)
        found = any(file_path in f for f in all_files)
        status = "[OK]" if found else "[MISSING]"
        print(f"{status} {file_path}")
        if not found:
            all_critical_present = False
    
    print("\n" + "=" * 60)
    if all_critical_present:
        print("[SUCCESS] TODOS LOS ARCHIVOS CRITICOS ESTAN PRESENTES")
    else:
        print("[ERROR] FALTAN ALGUNOS ARCHIVOS CRITICOS")
    print("=" * 60)

