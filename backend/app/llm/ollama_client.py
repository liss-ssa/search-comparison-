"""
Клиент для работы с Ollama (эмбеддинги и генерация).
Поддерживает работу через внешние туннели (Cloudflare, ngrok).
"""
from typing import List, Dict, Any
from app.config import settings
import logging
import time
from ollama import Client
from httpx import ConnectTimeout, ReadTimeout

logger = logging.getLogger(__name__)

# Настройки retry для работы через туннель
MAX_RETRIES = 3
RETRY_DELAY = 2  # секунды
REQUEST_TIMEOUT = 120  # секунд (для LLM генерации)


def _get_client() -> Client:
    """Создает клиент Ollama с увеличенным таймаутом."""
    return Client(
        host=settings.OLLAMA_URL,
        timeout=REQUEST_TIMEOUT
    )


def _retry_with_backoff(func, *args, **kwargs):
    """Выполняет функцию с retry-логикой."""
    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except (ConnectTimeout, ReadTimeout, Exception) as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (2 ** attempt)
                logger.warning(
                    f"Попытка {attempt + 1}/{MAX_RETRIES} не удалась: {e}. "
                    f"Повтор через {delay}с..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Все {MAX_RETRIES} попыток не удались")
    
    raise last_exception


def generate_answer(query: str, context: List[Dict[str, Any]]) -> str:
    """
    Генерирует ответ на вопрос пользователя на основе контекста.
    """
    # Формируем контекст из товаров
    context_text = "\n\n".join([
        f"Товар {i+1}:\n"
        f"Название: {item['name']}\n"
        f"Категория: {item['category']}\n"
        f"Бренд: {item['brand']}\n"
        f"Описание: {item['description']}\n"
        f"Цена: {item['price']} руб."
        for i, item in enumerate(context)
    ])
    
    # Формируем промпт
    prompt = f"""Ты — помощник в магазине косметики и бытовой химии. 
Ответь на вопрос пользователя, используя только информацию из предоставленного контекста.
Если в контексте нет подходящей информации, скажи об этом.

Контекст:
{context_text}

Вопрос пользователя: {query}

Ответ:"""
    
    try:
        client = _get_client()
        
        response = _retry_with_backoff(
            client.generate,
            model=settings.LLM_MODEL,
            prompt=prompt,
            options={
                "temperature": 0.7,
                "num_predict": 500
            }
        )
        
        answer = response["response"].strip()
        logger.info(f"LLM сгенерировал ответ длиной {len(answer)} символов")
        
        return answer
    
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return "Извините, произошла ошибка при генерации ответа."