from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class HealthResponse(BaseModel):
    """Ответ health check."""
    status: str
    version: str


class SearchQuery(BaseModel):
    """Запрос для поиска."""
    query: str = Field(..., min_length=1, max_length=500, description="Поисковый запрос")
    limit: int = Field(default=10, ge=1, le=100, description="Количество результатов")


class Product(BaseModel):
    """Модель товара."""
    id: int
    name: str
    category: str
    brand: str
    description: str
    price: float
    specs: Dict[str, Any]
    score: Optional[float] = None


class SearchResponse(BaseModel):
    """Ответ поиска."""
    query: str
    results: List[Product]
    total: int
    method: str


class CompareResponse(BaseModel):
    """Ответ сравнения методов поиска."""
    query: str
    bm25_results: List[Product]
    vector_results: List[Product]
    bm25_count: int
    vector_count: int


class AskRequest(BaseModel):
    """Запрос для RAG-ответа."""
    question: str = Field(..., min_length=1, max_length=500, description="Вопрос пользователя")
    top_k: int = Field(default=5, ge=1, le=20, description="Количество товаров для контекста")


class AskResponse(BaseModel):
    """Ответ RAG-системы."""
    question: str
    answer: str
    sources: List[Product]