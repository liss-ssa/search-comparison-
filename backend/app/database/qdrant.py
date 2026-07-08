"""
Инициализация Qdrant: создание коллекции для векторного поиска.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from app.config import settings
from app.llm.ollama_client import get_embedding
import logging

logger = logging.getLogger(__name__)


def init_qdrant():
    """Инициализация Qdrant: создание коллекции."""
    
    # Определяем, нужен ли HTTPS
    use_https = settings.QDRANT_HOST.endswith('.cloud.qdrant.io') or \
                settings.QDRANT_HOST.startswith('https://')
    
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY or None,
        https=use_https,
    )
    
    # Получаем размерность эмбеддинга
    try:
        test_embedding = get_embedding("test")
        vector_size = len(test_embedding)
        logger.info(f"Размерность эмбеддинга модели {settings.EMBED_MODEL}: {vector_size}")
    except Exception as e:
        logger.warning(f"Не удалось получить размерность эмбеддинга: {e}")
        logger.info("Используем размерность по умолчанию: 1024")
        vector_size = 1024
    
    # Создаем коллекцию
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if settings.QDRANT_COLLECTION not in collection_names:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        logger.info(f"Коллекция {settings.QDRANT_COLLECTION} создана (размерность: {vector_size})")
    else:
        logger.info(f"Коллекция {settings.QDRANT_COLLECTION} уже существует")