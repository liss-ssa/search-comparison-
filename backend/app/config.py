from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # PostgreSQL
    POSTGRES_HOST: str = Field(default="postgres", alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="search_db", alias="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="postgres", alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    
    # Qdrant
    QDRANT_HOST: str = Field(default="qdrant", alias="QDRANT_HOST")
    QDRANT_PORT: int = Field(default=6333, alias="QDRANT_PORT")
    QDRANT_COLLECTION: str = Field(default="products", alias="QDRANT_COLLECTION")
    QDRANT_API_KEY: str = Field(default="", alias="QDRANT_API_KEY")
    
    # Ollama
    OLLAMA_URL: str = Field(default="http://ollama:11434", alias="OLLAMA_URL")
    EMBED_MODEL: str = Field(default="nomic-embed-text", alias="EMBED_MODEL")
    LLM_MODEL: str = Field(default="llama3.1:latest", alias="LLM_MODEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()