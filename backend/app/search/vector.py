"""
Векторный поиск через Qdrant.
Использует эмбеддинги от dockhost AI Inference и cosine similarity.
"""
from qdrant_client import QdrantClient
from typing import List, Dict, Any
from app.config import settings
from app.llm.ollama_client import get_embedding
import logging
import time

logger = logging.getLogger(__name__)


def search_vector(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Выполняет векторный поиск через Qdrant.
    
    Args:
        query: Поисковый запрос
        limit: Максимальное количество результатов
    
    Returns:
        Список товаров с оценками сходства
    """
    start_time = time.time()
    
    try:
        # Получаем эмбеддинг запроса
        query_embedding = get_embedding(query)
        
        # Поддержка API ключа и HTTPS
        api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        use_https = settings.QDRANT_HOST.endswith('.cloud.qdrant.io') or \
                    settings.QDRANT_HOST.startswith('https://')
        
        client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=api_key,
            https=use_https
        )
        
        # Выполняем поиск
        search_result = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=limit
        )
        
        # Форматируем результаты
        formatted_results = []
        for hit in search_result:
            payload = hit.payload
            formatted_results.append({
                "id": hit.id,
                "name": payload.get("name"),
                "category": payload.get("category"),
                "brand": payload.get("brand"),
                "description": payload.get("description"),
                "price": float(payload.get("price", 0)),
                "specs": payload.get("specs", {}),
                "score": float(hit.score)
            })
        
        elapsed_time = time.time() - start_time
        logger.info(f"Vector: найдено {len(formatted_results)} результатов за {elapsed_time:.3f}s")
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Ошибка Vector поиска: {e}")
        return []