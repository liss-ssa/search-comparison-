import psycopg2
from psycopg2.extras import Json
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def init_postgres():
    """Инициализация PostgreSQL: создание таблицы и индексов."""
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )
    
    try:
        with conn.cursor() as cur:
            # Создаем таблицу products
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL,
                    specs JSONB,
                    search_vector tsvector
                )
            """)
            
            # Создаем GIN индекс для полнотекстового поиска
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_search 
                ON products USING GIN (search_vector)
            """)
            
            conn.commit()
            logger.info("PostgreSQL инициализирован")
    
    finally:
        conn.close()