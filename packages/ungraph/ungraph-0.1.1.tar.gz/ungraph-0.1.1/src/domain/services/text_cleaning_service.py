"""
Interfaz de Servicio: TextCleaningService

Define las operaciones para limpiar texto removiendo caracteres no deseados.
"""

from abc import ABC, abstractmethod
from typing import Optional


class TextCleaningService(ABC):
    """
    Interfaz que define las operaciones para limpiar texto.
    
    La limpieza puede incluir:
    - Remover acentos
    - Filtrar caracteres no permitidos
    - Normalizar espacios
    """
    
    @abstractmethod
    def clean(
        self,
        text: str,
        allowed_characters: Optional[str] = None,
        remove_accents: bool = True
    ) -> str:
        """
        Limpia un texto removiendo caracteres no deseados.
        
        Args:
            text: Texto a limpiar
            allowed_characters: Patrón de caracteres permitidos (opcional)
            remove_accents: Si True, remueve acentos (default: True)
        
        Returns:
            Texto limpio
        
        Raises:
            ValueError: Si el texto está vacío después de limpiar
        """
        pass

