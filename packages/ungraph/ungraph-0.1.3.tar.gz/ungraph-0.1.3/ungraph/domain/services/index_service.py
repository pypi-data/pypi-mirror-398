"""
Interfaz de Servicio: IndexService

Define las operaciones para crear y gestionar índices en el grafo.
"""

from abc import ABC, abstractmethod


class IndexService(ABC):
    """
    Interfaz que define las operaciones para crear índices en el grafo.
    
    Los índices pueden ser:
    - Vectoriales (para búsqueda por similitud)
    - Full-text (para búsqueda por texto)
    - Regulares (para búsquedas por propiedades)
    """
    
    @abstractmethod
    def setup_vector_index(
        self,
        index_name: str,
        node_label: str,
        property_name: str,
        dimensions: int
    ) -> None:
        """
        Crea un índice vectorial para búsqueda por similitud.
        
        Args:
            index_name: Nombre del índice
            node_label: Label de los nodos a indexar (ej: 'Chunk')
            property_name: Propiedad que contiene el vector (ej: 'embeddings')
            dimensions: Dimensión del vector (ej: 384)
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        pass
    
    @abstractmethod
    def setup_fulltext_index(
        self,
        index_name: str,
        node_label: str,
        property_name: str,
        analyzer: str = "spanish"
    ) -> None:
        """
        Crea un índice de texto completo.
        
        Args:
            index_name: Nombre del índice
            node_label: Label de los nodos a indexar (ej: 'Chunk')
            property_name: Propiedad que contiene el texto (ej: 'page_content')
            analyzer: Analizador de texto a usar (default: 'spanish')
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        pass
    
    @abstractmethod
    def setup_regular_index(
        self,
        index_name: str,
        node_label: str,
        property_name: str
    ) -> None:
        """
        Crea un índice regular para búsquedas por propiedad.
        
        Args:
            index_name: Nombre del índice
            node_label: Label de los nodos a indexar (ej: 'Chunk')
            property_name: Propiedad a indexar (ej: 'chunk_id_consecutive')
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        pass
    
    @abstractmethod
    def setup_all_indexes(self) -> None:
        """
        Configura todos los índices necesarios para el sistema.
        
        Este método debe crear todos los índices estándar:
        - Índice vectorial para embeddings
        - Índice full-text para page_content
        - Índice regular para chunk_id_consecutive
        """
        pass
    
    @abstractmethod
    def drop_index(self, index_name: str) -> None:
        """
        Elimina un índice específico.
        
        Args:
            index_name: Nombre del índice a eliminar
        
        Raises:
            ValueError: Si el índice no existe o no se puede eliminar
        """
        pass
    
    @abstractmethod
    def drop_all_indexes(self) -> None:
        """
        Elimina todos los índices creados por el sistema.
        
        Esto incluye:
        - Índices vectoriales
        - Índices full-text
        - Índices regulares
        """
        pass
    
    @abstractmethod
    def clean_graph(self, node_labels: list = None) -> None:
        """
        Limpia el grafo eliminando nodos y relaciones.
        
        Args:
            node_labels: Lista de labels de nodos a eliminar. 
                        Si es None, elimina todos los nodos y relaciones.
                        Si se especifica, solo elimina nodos con esos labels.
        
        Raises:
            Exception: Si ocurre un error durante la limpieza
        """
        pass

