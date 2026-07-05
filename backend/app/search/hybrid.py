"""
Гибридный поиск: комбинация BM25 и Vector.
"""
from typing import List, Dict, Any, Tuple
from app.search.bm25 import search_bm25
from app.search.vector import search_vector
import logging

logger = logging.getLogger(__name__)


def search_hybrid(query: str, limit: int = 10) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Выполняет гибридный поиск (BM25 + Vector).
    
    Args:
        query: Поисковый запрос
        limit: Максимальное количество результатов для каждого метода
    
    Returns:
        Кортеж (bm25_results, vector_results)
    """
    logger.info(f"Hybrid search для запроса: '{query}'")
    
    # Выполняем оба поиска
    bm25_results = search_bm25(query, limit)
    vector_results = search_vector(query, limit)
    
    return bm25_results, vector_results


def merge_results(
    bm25_results: List[Dict[str, Any]], 
    vector_results: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Объединяет результаты BM25 и Vector поиска.
    Использует простую стратегию: берем топ-K из каждого метода и объединяем.
    
    Args:
        bm25_results: Результаты BM25 поиска
        vector_results: Результаты Vector поиска
        top_k: Количество результатов от каждого метода
    
    Returns:
        Объединенный список уникальных товаров
    """
    seen_ids = set()
    merged = []
    
    # Добавляем топ-K из BM25
    for item in bm25_results[:top_k]:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            merged.append(item)
    
    # Добавляем топ-K из Vector
    for item in vector_results[:top_k]:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            merged.append(item)
    
    return merged