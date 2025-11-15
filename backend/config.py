"""
Centralized configuration management for NIRE.
Loads environment variables and provides typed access to settings.
"""

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Project Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    LOGS_DIR: Path = DATA_DIR / "logs"
    
    # LLM Configuration
    LLM_MODEL_PRIMARY: str = Field(..., description="Path to primary LLM model")
    LLM_MODEL_SECONDARY: str = Field(..., description="Path to secondary LLM model")
    LLM_N_GPU_LAYERS: int = Field(-1, description="Number of GPU layers (-1 = all)")
    LLM_N_CTX: int = Field(2048, description="Context window size")
    LLM_TEMPERATURE: float = Field(0.7, ge=0.0, le=2.0)
    
    # Database Configuration
    NEO4J_URI: str = Field(..., description="Neo4j connection URI")
    NEO4J_USER: str = Field(..., description="Neo4j username")
    NEO4J_PASSWORD: str = Field(..., description="Neo4j password")
    
    REDIS_HOST: str = Field("localhost", description="Redis host")
    REDIS_PORT: int = Field(6379, description="Redis port")
    REDIS_DB: int = Field(0, description="Redis database number")
    
    CHROMA_PERSIST_DIRECTORY: str = Field(..., description="ChromaDB storage path")
    
    # API Configuration
    API_HOST: str = Field("0.0.0.0", description="FastAPI host")
    API_PORT: int = Field(8000, description="FastAPI port")
    WS_PORT: int = Field(8765, description="WebSocket port")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )
    EMBEDDING_DEVICE: Literal["cuda", "cpu"] = Field("cuda", description="Device for embeddings")
    
    # Activity Monitor
    ACTIVITY_MONITOR_ENABLED: bool = Field(False, description="Enable system monitoring")
    ACTIVITY_MONITOR_INTERVAL: int = Field(60, description="Polling interval in seconds")
    
    # RAG Configuration
    RAG_SEARCH_PROVIDER: Literal["duckduckgo"] = Field("duckduckgo")
    RAG_MAX_RESULTS: int = Field(3, ge=1, le=10)
    RAG_REQUEST_TIMEOUT: int = Field(10, description="HTTP timeout in seconds")
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field("INFO")
    LOG_FILE: str = Field("./data/logs/nire.log")
    
    # Feature Flags
    FEATURE_MODEL_SWITCHING: bool = Field(True)
    FEATURE_STYLE_ADAPTATION: bool = Field(True)
    FEATURE_ACTIVITY_MONITOR: bool = Field(False)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Create necessary directories
settings.DATA_DIR.mkdir(exist_ok=True)
settings.LOGS_DIR.mkdir(exist_ok=True)
