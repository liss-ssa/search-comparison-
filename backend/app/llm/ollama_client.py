"""
Клиент для работы с dockhost AI Inference (OpenAI API совместимый).
Использует эмбеддинги и LLM через единый API.
"""
from openai import OpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    """Создает OpenAI клиент для dockhost AI Inference."""
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )


def get_embedding(text: str) -> list[float]:
    """Получает эмбеддинг текста через dockhost AI Inference."""
    try:
        client = _get_client()
        response = client.embeddings.create(
            model=settings.EMBED_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Ошибка получения эмбеддинга: {e}")
        raise


def generate_answer(query: str, context: list[dict]) -> str:
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
    
    try:
        client = _get_client()
        
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Ты — помощник в магазине косметики и бытовой химии. Ответь на вопрос пользователя, используя только информацию из предоставленного контекста. Если в контексте нет подходящей информации, скажи об этом."
                },
                {
                    "role": "user",
                    "content": f"Контекст:\n{context_text}\n\nВопрос пользователя: {query}"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        logger.info(f"LLM сгенерировал ответ длиной {len(answer)} символов")
        
        return answer
    
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return "Извините, произошла ошибка при генерации ответа."