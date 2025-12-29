"""
Interfaz de Servicio: PatternService

Define las operaciones para trabajar con patrones de grafo.
Esta interfaz está en el dominio porque el dominio define sus necesidades,
no cómo se implementan.

Referencias:
- Clean Architecture: Domain define interfaces, Infrastructure implementa
- GraphRAG Pattern Catalog: https://graphrag.com/reference/
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ungraph.domain.value_objects.graph_pattern import GraphPattern


class PatternService(ABC):
    """
    Servicio para trabajar con patrones de grafo.
    
    Este servicio permite:
    - Aplicar patrones al grafo (persistencia)
    - Generar queries Cypher dinámicamente
    - Validar que los patrones sean correctos
    
    Las implementaciones concretas estarán en infrastructure/.
    """
    
    @abstractmethod
    def apply_pattern(
        self,
        pattern: GraphPattern,
        data: Dict[str, Any]
    ) -> None:
        """
        Aplica un patrón al grafo con los datos proporcionados.
        
        Este método toma un patrón y datos, y persiste la estructura
        definida por el patrón en el grafo.
        
        Args:
            pattern: Patrón de grafo a aplicar
            data: Diccionario con los datos necesarios para el patrón
                 Las claves deben coincidir con las propiedades requeridas
                 de los nodos definidos en el patrón
        
        Raises:
            ValueError: Si el patrón es inválido o los datos son insuficientes
            RuntimeError: Si hay un error al aplicar el patrón
        """
        pass
    
    @abstractmethod
    def generate_cypher(
        self,
        pattern: GraphPattern,
        operation: str
    ) -> str:
        """
        Genera query Cypher dinámicamente basado en el patrón.
        
        Este método genera queries Cypher válidos para Neo4j basándose
        en la estructura del patrón.
        
        Args:
            pattern: Patrón de grafo
            operation: Tipo de operación ("create", "search", "update", "delete")
        
        Returns:
            Query Cypher como string (con placeholders $param para parámetros)
        
        Raises:
            ValueError: Si la operación no es soportada o el patrón es inválido
        
        Note:
            El query generado debe usar parámetros ($param) para todos los valores.
            No debe contener interpolación directa de strings.
        """
        pass
    
    @abstractmethod
    def validate_pattern(self, pattern: GraphPattern) -> bool:
        """
        Valida que un patrón sea correcto.
        
        Realiza validaciones adicionales más allá de las validaciones
        básicas del Value Object GraphPattern.
        
        Args:
            pattern: Patrón a validar
        
        Returns:
            True si el patrón es válido, False en caso contrario
        
        Raises:
            ValueError: Si el patrón tiene errores específicos que deben ser reportados
        """
        pass







