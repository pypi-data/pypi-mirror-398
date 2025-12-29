"""
Configuration management using Pydantic Settings.

This module provides global configuration management for Ungraph.
Supports both environment variables and programmatic configuration.

Variables are automatically loaded from:
1. Environment variables (with UNGRAPH_ prefix)
2. .env file (via python-dotenv)
3. Programmatic configuration (via configure() function)

Example .env file:
    UNGRAPH_OLLAMA_MODEL=llama3.2:3b
    UNGRAPH_OLLAMA_BASE_URL=http://127.0.0.1:11434
    UNGRAPH_OLLAMA_TEMPERATURE=0.0
    UNGRAPH_OLLAMA_NUM_GPU=1
    UNGRAPH_OLLAMA_NUM_THREAD=8
    UNGRAPH_NEO4J_URI=bolt://localhost:7687
    UNGRAPH_NEO4J_USER=neo4j
    UNGRAPH_NEO4J_PASSWORD=password

Example programmatic configuration:
    from .configuration import configure
    
    configure(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        neo4j_database="neo4j"
    )
"""

from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, Dict, Any
import os


# Load environment variables from .env file
load_dotenv(find_dotenv())


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All variables must be prefixed with UNGRAPH_ in the environment.
    For example: UNGRAPH_OLLAMA_MODEL, UNGRAPH_NEO4J_URI, etc.
    
    Can be overridden programmatically using configure() function.
    """
    model_config = SettingsConfigDict(
        env_prefix='UNGRAPH_',
        case_sensitive=False,  # Allow case-insensitive env vars
        env_file='.env',
        env_file_encoding='utf-8',
    )
    
    # Ollama Configuration
    ollama_model: Optional[str] = Field(
        default=None,
        description="Ollama model name (e.g., 'llama3.2:3b')"
    )
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Base URL for Ollama API"
    )
    ollama_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for Ollama model (0.0-2.0)"
    )
    ollama_num_gpu: int = Field(
        default=1,
        ge=0,
        description="Number of GPUs to use"
    )
    ollama_num_thread: int = Field(
        default=8,
        ge=1,
        description="Number of threads to use"
    )
    
    # Neo4j Configuration
    neo4j_uri: Optional[str] = Field(
        default=None,
        description="Neo4j connection URI (e.g., 'bolt://localhost:7687')"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: Optional[str] = Field(
        default=None,
        description="Neo4j password"
    )
    neo4j_database: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )
    
    # Storage Provider Configuration
    storage_provider: str = Field(
        default="neo4j",
        description="Storage provider (currently only 'neo4j' supported)"
    )
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Default embedding model"
    )

    # Inference Configuration
    inference_mode: str = Field(
        default="ner",
        description="Inference mode: 'ner' (spaCy NER baseline), 'llm' (semantic relations with LLM), or 'hybrid'"
    )


# Global settings instance
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings instance (singleton)
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def configure(**kwargs: Any) -> None:
    """
    Configure settings programmatically.
    
    This function allows setting configuration values programmatically,
    overriding environment variables. Values set here take precedence.
    
    Args:
        **kwargs: Configuration key-value pairs
        
    Example:
        >>> from src.core.configuration import configure
        >>> configure(
        ...     neo4j_uri="bolt://localhost:7687",
        ...     neo4j_password="mypassword",
        ...     neo4j_database="my_database"
        ... )
    """
    # Get current settings or create new
    current_settings = get_settings()
    
    # Update settings with provided values
    for key, value in kwargs.items():
        if hasattr(current_settings, key):
            setattr(current_settings, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")
    
    # Also update environment variables for compatibility
    for key, value in kwargs.items():
        env_key = f"UNGRAPH_{key.upper()}"
        os.environ[env_key] = str(value)


def reset_configuration() -> None:
    """
    Reset configuration to default (from environment variables).
    
    Useful for testing or resetting programmatic changes.
    """
    global _settings_instance
    _settings_instance = None


# Default settings instance
settings = get_settings()