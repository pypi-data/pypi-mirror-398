"""
Punto de entrada principal de la aplicación.

Ejemplo de uso del caso de uso IngestDocumentUseCase.
"""

from pathlib import Path
from ungraph.application.dependencies import create_ingest_document_use_case


def main():
    """
    Función principal que demuestra el uso del caso de uso.
    
    Ejemplo:
        python -m src.main
    """
    # Crear caso de uso usando el Composition Root
    use_case = create_ingest_document_use_case()
    
    # Ejemplo: Ingerir un archivo Markdown
    file_path = Path("src/data/110225.md")
    
    if not file_path.exists():
        print(f"Archivo no encontrado: {file_path}")
        print("Por favor, asegúrate de que el archivo existe.")
        return
    
    try:
        # Ejecutar el caso de uso
        chunks = use_case.execute(
            file_path=file_path,
            chunk_size=1000,
            chunk_overlap=200,
            clean_text=True
        )
        
        print(f"\n✅ Documento ingerido exitosamente!")
        print(f"   Archivo: {file_path.name}")
        print(f"   Chunks creados: {len(chunks)}")
        print(f"   Chunks con embeddings: {sum(1 for c in chunks if c.embeddings)}")
        
    except Exception as e:
        print(f"\n❌ Error al ingerir documento: {e}")
        raise
    finally:
        # Limpiar recursos
        if hasattr(use_case.chunk_repository, 'close'):
            use_case.chunk_repository.close()
        if hasattr(use_case.index_service, 'close'):
            use_case.index_service.close()


if __name__ == "__main__":
    main()

