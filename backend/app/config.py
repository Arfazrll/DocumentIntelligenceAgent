"""
DocIntel AI — Application Configuration.

Loads all settings from environment variables / .env file.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = BASE_DIR / "data" / "docintel.db"
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{DB_FILE.as_posix()}"

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database (SQLite)
    DATABASE_URL: str = DEFAULT_DB_URL

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "documents"

    # Ollama (Local LLM)
    USE_LOCAL_LLM: bool = True
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3"
    OLLAMA_VERIFIER_MODEL: str = "qwen2.5:0.5b"
    OLLAMA_FALLBACK_MODEL: str = "qwen2.5:0.5b"

    # Groq API (Reasoning LLM)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Gemini API (Extraction LLM)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"

    # Langfuse Observability
    LANGFUSE_HOST: str = "http://langfuse:3000"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""

    # System Config
    MAX_UPLOAD_SIZE_MB: int = 100
    MAX_FILES_PER_UPLOAD: int = 10
    CHUNK_SIZE_TOKENS: int = 800
    CHUNK_OVERLAP_TOKENS: int = 100
    RETRIEVAL_TOP_K_INITIAL: int = 20
    RETRIEVAL_TOP_K_FINAL: int = 5
    CONFIDENCE_THRESHOLD: float = 0.70
    RETRIEVAL_FUSION_ALPHA: float = 0.6
    RETRIEVAL_MIN_RELEVANCE: float = 0.3

    # Paths
    DOCUMENTS_DIR: str = "/app/documents"
    DATA_DIR: str = "/app/data"

    @property
    def documents_path(self) -> Path:
        """Get documents directory as Path."""
        path = Path(self.DOCUMENTS_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_path(self) -> Path:
        """Get data directory as Path."""
        path = Path(self.DATA_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

# Singleton instance
settings = Settings()
