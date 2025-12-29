from dataclasses import dataclass
from typing import Dict, Any, Optional, List
@dataclass
class Page:
    """Representa una página dentro de un archivo"""
    filename: str  # Referencia al File
    page_number: int
    media_content: Optional[str] = None
    
    def __post_init__(self):
        if self.page_number < 1:
            raise ValueError("Page number must be positive")