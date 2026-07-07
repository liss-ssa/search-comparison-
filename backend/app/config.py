from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # PostgreSQL
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="search_db")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    
    # Qdrant
    QDRANT_HOST: str = Field(default="qdrant")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_COLLECTION: str = Field(default="products")
    QDRANT_API_KEY: str = Field(default="")
    
    # OpenAI (dockhost AI Inference)
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_BASE_URL: str = Field(default="https://inference.dockhost.io/v1")
    EMBED_MODEL: str = Field(default="intfloat/multilingual-e5-large")
    LLM_MODEL: str = Field(default="deepseek/deepseek-v3.2")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()