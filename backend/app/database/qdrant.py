from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from app.config import settings
import logging
from ollama import Client

logger = logging.getLogger(__name__)


def init_qdrant():
    """Инициализация Qdrant: создание коллекции."""
    # Поддержка API ключа (если задан)
    api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
    
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY,
    )
    
    # Получаем размерность эмбеддинга через Ollama Client
    try:
        from app.llm.ollama_client import _get_client, _retry_with_backoff
        ollama_client = _get_client()
        test_response = _retry_with_backoff(
            ollama_client.embeddings,
            model=settings.EMBED_MODEL,
            prompt="test"
        )
        vector_size = len(test_response["embedding"])
        logger.info(f"Размерность эмбеддинга модели {settings.EMBED_MODEL}: {vector_size}")
    except Exception as e:
        logger.warning(f"Не удалось получить размерность эмбеддинга: {e}")
        logger.info("Используем размерность по умолчанию: 1024 (для bge-m3)")
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