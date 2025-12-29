"""
Implementación: SimpleTextCleaningService

Implementa TextCleaningService usando unicodedata y regex.
Envuelve el código existente del notebook.
"""

import unicodedata
import re
import logging
from typing import Optional

from domain.services.text_cleaning_service import TextCleaningService

logger = logging.getLogger(__name__)


class SimpleTextCleaningService(TextCleaningService):
    """
    Implementación simple de TextCleaningService.
    
    Limpia texto removiendo caracteres no deseados y acentos.
    """
    
    def clean(
        self,
        text: str,
        allowed_characters: Optional[str] = None,
        remove_accents: bool = True
    ) -> str:
        """
        Limpia un texto removiendo caracteres no deseados.
        
        Basado en clean_text del notebook.
        """
        logger.info("Starting text cleaning.")
        
        if remove_accents:
            # Remover acentos
            text = unicodedata.normalize("NFD", text)
            text = text.encode("ascii", "ignore").decode("utf-8")
        
        if allowed_characters is None:
            allowed_characters = "a-zA-Z0-9áéíóúÁÉÍÓÚñÑ.,;:!?'\"()\\[\\]{}<>\\-\\_@#%&/\\s"
        
        # Crear patrón para caracteres no permitidos
        pattern = f"[^{allowed_characters}]"
        
        # Reemplazar caracteres no permitidos
        cleaned_text = re.sub(pattern, " ", text)
        
        # Remover espacios duplicados
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        
        logger.info("Text cleaning completed.")
        return cleaned_text

