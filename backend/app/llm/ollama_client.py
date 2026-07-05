"""
Клиент для работы с Ollama (эмбеддинги и генерация).
"""
from typing import List, Dict, Any
from app.config import settings
import logging
from ollama import Client

logger = logging.getLogger(__name__)


def generate_answer(query: str, context: List[Dict[str, Any]]) -> str:
    """
    Генерирует ответ на вопрос пользователя на основе контекста.
    
    Args:
        query: Вопрос пользователя
        context: Список товаров для контекста
    
    Returns:
        Сгенерированный ответ
    """
    # Формируем контекст из товаров
    context_text = "\n\n".join([
        f"Товар {i+1}:\n"
        f"Название: {item['name']}\n"
        "Категория: {category}\n"
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
        # Создаем клиент с указанием host
        client = Client(host=settings.OLLAMA_URL)
        
        # Вызываем generate БЕЗ параметра host
        response = client.generate(
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