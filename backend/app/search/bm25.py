"""
BM25 поиск через PostgreSQL tsvector.
Использует полнотекстовый поиск с русским стеммером.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from app.config import settings
import logging
import time

logger = logging.getLogger(__name__)


def search_bm25(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Выполняет BM25 поиск через PostgreSQL.
    
    Args:
        query: Поисковый запрос
        limit: Максимальное количество результатов
    
    Returns:
        Список товаров с оценками релевантности
    """
    start_time = time.time()
    
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Пытаемся строгий поиск (AND)
            cur.execute(
                """
                SELECT 
                    id,
                    name,
                    category,
                    brand,
                    description,
                    price,
                    specs,
                    ts_rank(search_vector, websearch_to_tsquery('russian', %s)) as rank
                FROM products
                WHERE search_vector @@ websearch_to_tsquery('russian', %s)
                ORDER BY rank DESC
                LIMIT %s
                """,
                (query, query, limit)
            )
            
            results = cur.fetchall()
            
            # Если строгий поиск ничего не дал, используем мягкий (OR)
            if not results:
                logger.info(f"BM25: строгий поиск не дал результатов, используем OR")
                cur.execute(
                    """
                    SELECT 
                        id,
                        name,
                        category,
                        brand,
                        description,
                        price,
                        specs,
                        ts_rank(search_vector, to_tsquery('russian', %s)) as rank
                    FROM products
                    WHERE search_vector @@ to_tsquery('russian', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                    """,
                    (' | '.join(query.split()), ' | '.join(query.split()), limit)
                )
                results = cur.fetchall()
            
            # Форматируем результаты
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "id": row["id"],
                    "name": row["name"],
                    "category": row["category"],
                    "brand": row["brand"],
                    "description": row["description"],
                    "price": float(row["price"]),
                    "specs": row["specs"],
                    "score": float(row["rank"]) if row["rank"] else 0.0
                })
            
            elapsed_time = time.time() - start_time
            logger.info(f"BM25: найдено {len(formatted_results)} результатов за {elapsed_time:.3f}s")
            
            return formatted_results
    
    except Exception as e:
        logger.error(f"Ошибка BM25 поиска: {e}")
        return []
    
    finally:
        conn.close()