from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.postgres import init_postgres
from app.database.qdrant import init_qdrant
from app.models.schemas import (
    HealthResponse, 
    SearchQuery, 
    SearchResponse, 
    CompareResponse,
    AskRequest,
    AskResponse
)
from app.search.bm25 import search_bm25
from app.search.vector import search_vector
from app.search.hybrid import search_hybrid
from app.llm.ollama_client import generate_answer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте приложения."""
    logger.info("Инициализация баз данных...")
    init_postgres()
    init_qdrant()
    logger.info("Базы данных инициализированы")
    yield
    logger.info("Завершение работы")


app = FastAPI(
    title="Search Comparison API",
    description="Сравнение BM25 и Vector поиска для косметики и бытовой химии",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса."""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/seed")
async def seed_data():
    """Ручной запуск генерации и загрузки данных."""
    try:
        from app.utils.seed_data import main as seed_main
        seed_main()
        return {"status": "success", "message": "Данные успешно загружены"}
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/bm25", response_model=SearchResponse)
async def search_bm25_endpoint(request: SearchQuery):
    """
    BM25 поиск через PostgreSQL.
    Использует полнотекстовый поиск с русским стеммером.
    """
    try:
        results = search_bm25(request.query, request.limit)
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            method="bm25"
        )
    except Exception as e:
        logger.error(f"Ошибка BM25 поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/vector", response_model=SearchResponse)
async def search_vector_endpoint(request: SearchQuery):
    """
    Векторный поиск через Qdrant.
    Использует эмбеддинги от Ollama и cosine similarity.
    """
    try:
        results = search_vector(request.query, request.limit)
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            method="vector"
        )
    except Exception as e:
        logger.error(f"Ошибка Vector поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare", response_model=CompareResponse)
async def compare_search(request: SearchQuery):
    """
    Сравнение BM25 и Vector поиска.
    Возвращает результаты обоих методов для наглядного сравнения.
    """
    try:
        bm25_results, vector_results = search_hybrid(request.query, request.limit)
        return CompareResponse(
            query=request.query,
            bm25_results=bm25_results,
            vector_results=vector_results,
            bm25_count=len(bm25_results),
            vector_count=len(vector_results)
        )
    except Exception as e:
        logger.error(f"Ошибка сравнения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    RAG-ответ на вопрос пользователя.
    Использует векторный поиск для получения контекста и LLM для генерации ответа.
    """
    try:
        # Получаем контекст через векторный поиск
        context = search_vector(request.question, request.top_k)
        
        if not context:
            return AskResponse(
                question=request.question,
                answer="Не удалось найти подходящие товары в каталоге.",
                sources=[]
            )
        
        # Генерируем ответ через LLM
        answer = generate_answer(request.question, context)
        
        return AskResponse(
            question=request.question,
            answer=answer,
            sources=context
        )
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        raise HTTPException(status_code=500, detail=str(e))