#!/usr/bin/env python
"""Script para verificar la instalación del paquete desde wheel."""

import sys
import importlib
from pathlib import Path

def test_import(module_name: str, description: str) -> bool:
    """Intenta importar un módulo y retorna True si tiene éxito."""
    try:
        importlib.import_module(module_name)
        print(f"[OK] {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"[ERROR] {description}: {module_name} - {e}")
        return False
    except Exception as e:
        print(f"[WARNING] {description}: {module_name} - {e}")
        return False

def main():
    """Ejecuta verificaciones de instalación."""
    print("=" * 60)
    print("VERIFICACION DE INSTALACION DESDE WHEEL")
    print("=" * 60)
    print(f"\nPython version: {sys.version}")
    print(f"Python path: {sys.executable}")
    
    # Verificar imports básicos
    print("\n" + "=" * 60)
    print("VERIFICACION DE IMPORTS BASICOS")
    print("=" * 60)
    
    basic_imports = [
        ("ungraph", "Paquete principal"),
        ("ungraph.domain", "Módulo domain"),
        ("ungraph.application", "Módulo application"),
        ("ungraph.infrastructure", "Módulo infrastructure"),
        ("ungraph.core", "Módulo core"),
    ]
    
    basic_results = []
    for module, desc in basic_imports:
        basic_results.append(test_import(module, desc))
    
    # Verificar entidades críticas
    print("\n" + "=" * 60)
    print("VERIFICACION DE ENTIDADES CRITICAS")
    print("=" * 60)
    
    entity_imports = [
        ("ungraph.domain.entities.fact", "Entidad Fact"),
        ("ungraph.domain.entities.entity", "Entidad Entity"),
        ("ungraph.domain.entities.relation", "Entidad Relation"),
        ("ungraph.domain.services.inference_service", "Servicio InferenceService"),
    ]
    
    entity_results = []
    for module, desc in entity_imports:
        entity_results.append(test_import(module, desc))
    
    # Verificar implementaciones
    print("\n" + "=" * 60)
    print("VERIFICACION DE IMPLEMENTACIONES")
    print("=" * 60)
    
    impl_imports = [
        ("ungraph.infrastructure.services.spacy_inference_service", "SpacyInferenceService"),
        ("ungraph.application.use_cases.ingest_document", "IngestDocumentUseCase"),
        ("ungraph.application.dependencies", "Dependencies"),
    ]
    
    impl_results = []
    for module, desc in impl_imports:
        impl_results.append(test_import(module, desc))
    
    # Verificar que las clases se pueden instanciar (sin ejecutar)
    print("\n" + "=" * 60)
    print("VERIFICACION DE CLASES")
    print("=" * 60)
    
    try:
        from ungraph.domain.entities.fact import Fact
        print("[OK] Clase Fact importable")
    except Exception as e:
        print(f"[ERROR] Clase Fact: {e}")
    
    try:
        from ungraph.domain.services.inference_service import InferenceService
        print("[OK] Interfaz InferenceService importable")
    except Exception as e:
        print(f"[ERROR] Interfaz InferenceService: {e}")
    
    # Resumen final
    print("\n" + "=" * 60)
    total_tests = len(basic_results) + len(entity_results) + len(impl_results)
    passed_tests = sum(basic_results) + sum(entity_results) + sum(impl_results)
    
    if passed_tests == total_tests:
        print(f"[SUCCESS] TODAS LAS VERIFICACIONES PASARON ({passed_tests}/{total_tests})")
    else:
        print(f"[WARNING] ALGUNAS VERIFICACIONES FALLARON ({passed_tests}/{total_tests})")
    print("=" * 60)
    
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())




