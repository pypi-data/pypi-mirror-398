

from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from datetime import datetime


@dataclass
class File:
    """Representa un archivo en el sistema"""
    filename: str
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.filename:
            raise ValueError("Filename cannot be empty")