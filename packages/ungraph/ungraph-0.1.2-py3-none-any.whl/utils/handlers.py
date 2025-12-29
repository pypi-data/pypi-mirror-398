from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger("Ungraph Handlers") 


def find_in_project(
    target: str,
    search_type: str = "folder",
    project_root: Optional[Union[str, Path]] = None) -> Path:
    """
    Función maestra para buscar carpetas o archivos en un proyecto.
    
    Args:
        target: Nombre del elemento a buscar o patrón glob
        search_type: Tipo de búsqueda - "folder" o "pattern"
        project_root: Raíz del proyecto. Si es None, se busca automáticamente.
        
    Returns:
        Path: Ruta absoluta al elemento encontrado
        
    Raises:
        FileNotFoundError: Si no se encuentra el elemento o la raíz del proyecto
    """
    
    # Encontrar raíz del proyecto si no se especifica
    if project_root is None:
        project_root = find_project_root()
    else:
        project_root = Path(project_root).resolve()
    
    if not project_root.exists():
        raise FileNotFoundError(f"Directorio del proyecto no existe: {project_root}")
    
    found_item = None
    
    if search_type == "pattern":
        # Búsqueda por patrón glob
        matches = list(project_root.glob(target))
        if matches:
            found_item = matches[0].resolve()
    
    elif search_type == "folder":
        # Búsqueda recursiva por nombre de carpeta
        for item in project_root.rglob("*"):
            if item.is_dir() and item.name == target:
                found_item = item.resolve()
                break
    
    if found_item is None:
        raise FileNotFoundError(f"No se encontró '{target}' de tipo '{search_type}' en: {project_root}")
    
    logger.info(f"Encontrado: {found_item}")
    return found_item


def find_project_root(start_path: Optional[Union[str, Path]] = None, file_path: Optional[str] = None) -> Path:
    """
    Encuentra la raíz del proyecto buscando archivos indicadores.
    
    Esta función es completamente agnóstica y funciona desde cualquier ubicación.
    Busca hacia arriba desde el punto de partida hasta encontrar un indicador de raíz.
    
    Args:
        start_path: Ruta desde donde empezar a buscar. Si es None, usa el directorio actual.
        file_path: Ruta de un archivo (típicamente __file__). Si se provee, busca desde ese archivo.
                   Tiene prioridad sobre start_path.
        
    Returns:
        Path: Ruta absoluta a la raíz del proyecto
        
    Raises:
        FileNotFoundError: Si no se encuentra la raíz del proyecto
        
    Examples:
        >>> # Desde un script
        >>> root = find_project_root(file_path=__file__)
        >>> # Desde cualquier ubicación
        >>> root = find_project_root()
    """
    # Si se provee file_path, usarlo como punto de partida (más agnóstico)
    if file_path is not None:
        start_path = Path(file_path).resolve().parent
    elif start_path is None:
        start_path = Path.cwd()
    
    current_path = Path(start_path).resolve()
    
    # Archivos indicadores de raíz de proyecto
    root_indicators = [
        'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt',
        'Pipfile', 'poetry.lock', 'package.json', 'Cargo.toml', 'go.mod', '.git'
    ]
    
    # Buscar hacia arriba desde el directorio actual
    for path in [current_path] + list(current_path.parents):
        for indicator in root_indicators:
            if (path / indicator).exists():
                logger.debug(f"Proyecto root encontrado en: {path} (indicador: {indicator})")
                return path
    
    raise FileNotFoundError(f"No se encontró la raíz del proyecto desde: {current_path}")


def detect_encoding(file_path: Path, sample_size: int = 10000) -> str:
    """
    Detecta automáticamente la codificación de un archivo de texto.
    
    Parameters:
    -----------
    file_path : Path
        Ruta al archivo a analizar
    sample_size : int, optional
        Tamaño de la muestra a leer para detectar la codificación (default: 10000 bytes)
    
    Returns:
    --------
    str
        Nombre de la codificación detectada
    """
    # Lista de codificaciones comunes a probar como fallback
    fallback_encodings = ['utf-8', 'windows-1252', 'latin-1', 'iso-8859-1', 'cp1252']
    
    # Intentar usar chardet si está disponible
    try:
        import chardet
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
            result = chardet.detect(sample)
            if result['encoding'] and result['confidence'] > 0.7:
                detected_encoding = result['encoding'].lower()
                logger.info(f"Codificación detectada por chardet: {detected_encoding} (confianza: {result['confidence']:.2%})")
                return detected_encoding
    except ImportError:
        logger.debug("chardet no está instalado, usando método de fallback")
    except Exception as e:
        logger.warning(f"Error al detectar codificación con chardet: {e}, usando método de fallback")
    
    # Método de fallback: probar codificaciones comunes
    logger.info("Intentando detectar codificación mediante prueba de lectura...")
    for enc in fallback_encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(sample_size)
            logger.info(f"Codificación detectada por prueba: {enc}")
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            continue
    
    # Si ninguna funciona, retornar utf-8 como default
    logger.warning("No se pudo detectar la codificación, usando utf-8 como default")
    return 'utf-8'