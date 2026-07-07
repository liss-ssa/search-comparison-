"""
Генерация синтетического каталога косметики и бытовой химии.
Загрузка данных в PostgreSQL и Qdrant.
"""
import json
import random
from typing import List, Dict, Any
import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import psycopg2
from psycopg2.extras import Json
from ollama import Client

import logging
logger = logging.getLogger(__name__)

from ..config import settings


# === ГЕНЕРАЦИЯ ДАННЫХ ===

BRANDS = {
    "шампуни": ["Pantene", "Head & Shoulders", "Natura Siberica", "Чистая Линия", "Elseve", "Syoss"],
    "гели для душа": ["Nivea", "Dove", "Palmolive", "Le Petit Marseillais", "Yves Rocher"],
    "кремы для лица": ["Nivea", "L'Oreal", "Garnier", "Черный Жемчуг", "Vichy", "La Roche-Posay"],
    "кремы для тела": ["Nivea", "Dove", "Neutrogena", "Vaseline", "Johnson's"],
    "стиральные порошки": ["Ariel", "Tide", "Persil", "Миф", "Ушастый Нянь", "BiMax"],
    "средства для посуды": ["Fairy", "Sorti", "AOS", "Pril", "Synergetic"],
    "чистящие средства": ["Cillit Bang", "Domestos", "Comet", "Sif", "Sanita"],
    "зубные пасты": ["Colgate", "Blend-a-med", "Splat", "ROCS", "President", "Lacalut"],
    "дезодоранты": ["Rexona", "Nivea", "Dove", "Old Spice", "Fa", "Secret"]
}

CATEGORY_TEMPLATES = {
    "шампуни": {
        "descriptions": [
            "Шампунь для {тип_волос} волос с {ингредиент}. Бережно очищает и питает.",
            "Восстанавливающий шампунь с {ингредиент} для {тип_волос} волос. Страна изготовления {страна}",
            "Профессиональный шампунь для {тип_волос} волос. Придает блеск и объем.",
            "Увлажняющий шампунь с натуральным {ингредиент} для ежедневного использования. Объем {объем_мл} мл."
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([250, 400, 500, 750]),
            "тип_волос": random.choice(["сухих", "жирных", "нормальных", "окрашенных", "поврежденных"]),
            "ингредиент": random.choice(["кератином", "аргановым маслом", "пантенолом", "экстрактом ромашки", "кокосовым маслом"]),
            "страна": random.choice(["Россия", "Франция", "Германия", "Польша"])
        }
    },
    "гели для душа": {
        "descriptions": [
            "Гель для душа с ароматом {аромат}. Нежная формула для {тип_кожи} кожи.",
            "Увлажняющий гель для душа с ароматом {аромат}. Оставляет кожу мягкой и шелковистой. В объеме {объем_мл} мл.",
            "Тонизирующий гель для душа с экстрактом {аромат}. Заряд бодрости на весь день.",
            "Питательный гель для душа {аромат} с маслом ши. Подходит для {тип_кожи}"
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([250, 400, 500]),
            "аромат": random.choice(["лаванды", "ванили", "цитрусовых", "мяты", "зеленого чая", "персика"]),
            "тип_кожи": random.choice(["нормальная", "сухая", "чувствительная", "все типы"])
        }
    },
    "кремы для лица": {
        "descriptions": [
            "Дневной крем для лица {тип_кожи} с {активный_ингредиент}. Защищает от сухости.",
            "Ночной восстанавливающий крем с {активный_ингредиент} для {тип_кожи} кожи. Объем {объем_мл} мл.",
            "Увлажняющий крем для лица с SPF {spf} и {активный_ингредиент}.",
            "Антивозрастной крем {возраст} с гиалуроновой кислотой. Объем {объем_мл} мл."
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([30, 50, 75, 100]),
            "тип_кожи": random.choice(["сухая", "жирная", "комбинированная", "чувствительная", "нормальная"]),
            "активный_ингредиент": random.choice(["гиалуроновой кислотой", "витамином C", "ретинолом", "коллагеном", "ниацинамидом"]),
            "spf": random.choice([0, 15, 30, 50]),
            "возраст": random.choice(["25+", "35+", "45+", "55+"])
        }
    },
    "кремы для тела": {
        "descriptions": [
            "Крем для тела {аромат} с маслом {масло}. Глубокое увлажнение на 24 часа.",
            "Питательный крем для тела с {масло} и витамином E. Объем {объем_мл} мл.",
            "Легкий крем для тела {аромат}. Быстро впитывается, не оставляет жирности.",
            "Интенсивно увлажняющий крем для очень сухой кожи с {масло}. Объем {объем_мл} мл."
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([200, 300, 400, 500]),
            "аромат": random.choice(["нейтральный", "кокос", "миндаль", "ши", "какао"]),
            "масло": random.choice(["ши", "кокосовое", "миндальное", "оливковое", "жожоба"])
        }
    },
    "стиральные порошки": {
        "descriptions": [
            "Стиральный порошок {тип_стирки} для {тип_ткани}. Удаляет даже стойкие пятна. Вес {вес_кг} кг.",
            "Концентрированный порошок для {тип_ткани}. Экономичный расход.",
            "Детский стиральный порошок {тип_стирки} гипоаллергенный. Безопасен для чувствительной кожи.",
            "Универсальный порошок {тип_стирки} для белого и цветного. Сохраняет яркость. Вес {вес_кг} кг."
        ],
        "характеристики": lambda: {
            "вес_кг": random.choice([0.4, 0.8, 1.5, 2.4, 3.0]),
            "тип_стирки": random.choice(["автомат", "ручная", "универсальный"]),
            "тип_ткани": random.choice(["хлопка", "синтетики", "смешанной ткани", "деликатной ткани", "всех типов"])
        }
    },
    "средства для посуды": {
        "descriptions": [
            "Средство для мытья посуды {концентрация}. Эффективно удаляет жир с первого раза.",
            "Концентрированное средство {аромат}. Хватает на дольше. Объем {объем_мл} мл.",
            "Гипоаллергенное средство для посуды с концентрацией {концентрация}. Безопасно для детской посуды.",
            "Эко-средство для посуды {аромат} на растительной основе. Объем {объем_мл} мл."
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([450, 900, 1500]),
            "аромат": random.choice(["лимон", "яблоко", "лайм", "нейтральный", "мята"]),
            "концентрация": random.choice(["стандартная", "концентрированная", "ультра"])
        }
    },
    "чистящие средства": {
        "descriptions": [
            "Чистящее средство {форма} для {поверхность}. Объем {объем_мл} мл. Удаляет известковый налет и ржавчину.",
            "Антибактериальное средство {форма} для {поверхность}. Убивает 99.9% бактерий.",
            "Универсальное чистящее средство {форма} для всех поверхностей в доме. Объем {объем_мл} мл.",
            "Крем-чистящее средство {форма} для {поверхность}. Не царапает поверхность."
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([500, 750, 1000]),
            "форма": random.choice(["спрей", "гель", "крем", "порошок"]),
            "поверхность": random.choice(["ванна и душ", "кухня", "унитаз", "плитка", "стекло", "универсальное"])
        }
    },
    "зубные пасты": {
        "descriptions": [
            "Зубная паста {эффект} {содержит_фтор}. Защита от кариеса на 12 часов. Для возраста {возраст}.",
            "Отбеливающая паста {эффект} с микрогранулами. Возвращает естественную белизну. Для возраста {возраст}.",
            "Паста для чувствительных зубов {эффект}. Объем {объем_мл} мл. Снижает чувствительность за 2 недели.",
            "Натуральная зубная паста {эффект} без фтора с {содержит_фтор}. Объем {объем_мл} мл."
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([50, 75, 100, 125]),
            "эффект": random.choice(["отбеливание", "защита от кариеса", "свежесть дыхания", "укрепление десен", "комплексная защита"]),
            "возраст": random.choice(["взрослая", "6+", "12+"]),
            "содержит_фтор": random.choice(["с содержание фтора", "без фтора"])
        }
    },
    "дезодоранты": {
        "descriptions": [
            "Дезодорант {тип} {аромат}. Защита от пота и запаха на 48 часов.",
            "Антиперспирант {тип} {аромат} с объемом {объем_мл} мл. Не оставляет следов.",
            "Дезодорант-стик {аромат} для чувствительной кожи. Без спирта и парабенов.",
            "Спрей-дезодорант {аромат} с увлажняющим комплексом. Объем {объем_мл} мл."
        ],
        "характеристики": lambda: {
            "объем_мл": random.choice([50, 75, 150, 200]),
            "тип": random.choice(["спрей", "стик", "ролл-он", "крем"]),
            "аромат": random.choice(["свежесть", "пудра", "цитрус", "нейтральный", "цветочный"])
        }
    }
}


def generate_products(count_per_category: int = 10) -> List[Dict[str, Any]]:
    """Генерирует каталог товаров"""
    products = []
    product_id = 1
    
    for category, template in CATEGORY_TEMPLATES.items():
        brands = BRANDS[category]
        
        for i in range(count_per_category):
            brand = random.choice(brands)
            description_template = random.choice(template["descriptions"])
            
            # Генерируем характеристики
            specs = template["характеристики"]()
            
            # Формируем описание, подставляя характеристики
            description = description_template.format(**specs)
            
            # Генерируем название
            name = f"{brand} {category.replace('_', ' ').title()} {specs.get('объем_мл', specs.get('вес_кг', ''))}{'мл' if 'объем_мл' in specs else 'кг'}"
            
            # Генерируем цену (зависит от категории)
            base_prices = {
                "шампуни": (200, 800),
                "гели для душа": (150, 600),
                "кремы для лица": (300, 2500),
                "кремы для тела": (200, 1200),
                "стиральные порошки": (150, 900),
                "средства для посуды": (100, 500),
                "чистящие средства": (150, 700),
                "зубные пасты": (100, 600),
                "дезодоранты": (150, 700)
            }
            min_price, max_price = base_prices[category]
            price = round(random.uniform(min_price, max_price), 2)
            
            product = {
                "id": product_id,
                "название": name,
                "категория": category,
                "бренд": brand,
                "описание": description,
                "цена": price,
                "характеристики": specs
            }
            
            products.append(product)
            product_id += 1
    
    random.shuffle(products)  # Перемешиваем для реалистичности
    return products


# === ЗАГРУЗКА В БАЗЫ ДАННЫХ ===

def seed_postgres(products: List[Dict[str, Any]]) -> None:
    """Загружает товары в PostgreSQL"""
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )
    
    try:
        with conn.cursor() as cur:
            # Очищаем таблицу
            cur.execute("DELETE FROM products")
            
            # Вставляем товары
            for product in products:
                cur.execute(
                    """
                    INSERT INTO products (id, name, category, brand, description, price, specs)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        product["id"],
                        product["название"],
                        product["категория"],
                        product["бренд"],
                        product["описание"],
                        product["цена"],
                        Json(product["характеристики"])
                    )
                )
            
            # Обновляем search_vector для полнотекстового поиска
            cur.execute(
                """
                UPDATE products
                SET search_vector = 
                    setweight(to_tsvector('russian', coalesce(name, '')), 'A') ||
                    setweight(to_tsvector('russian', coalesce(category, '')), 'B') ||
                    setweight(to_tsvector('russian', coalesce(brand, '')), 'B') ||
                    setweight(to_tsvector('russian', coalesce(description, '')), 'C')
                """
            )
            
            conn.commit()
            print(f"Загружено {len(products)} товаров в PostgreSQL")
    
    finally:
        conn.close()


def seed_qdrant(products: List[Dict[str, Any]]) -> None:
    """Загружает товары в Qdrant с эмбеддингами."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    from app.llm.ollama_client import _get_client, _retry_with_backoff
    
    # Поддержка API ключа
    api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
    
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=api_key
    )
    
    ollama_client = _get_client()
    
    # Генерируем эмбеддинги через Ollama
    print("Генерация эмбеддингов через Ollama...")
    embeddings = []
    
    for i, product in enumerate(products):
        # Формируем текст для эмбеддинга
        text = f"{product['название']}. {product['описание']}"
        
        # Получаем эмбеддинг с retry
        try:
            response = _retry_with_backoff(
                ollama_client.embeddings,
                model=settings.EMBED_MODEL,
                prompt=text
            )
            embedding = response["embedding"]
            embeddings.append(embedding)
        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддинга для товара {product['id']}: {e}")
            # Используем нулевой вектор как fallback
            embeddings.append([0.0] * 1024)
        
        if (i + 1) % 10 == 0:
            print(f"  Обработано {i + 1}/{len(products)} товаров")
    
    # Загружаем в Qdrant
    points = []
    for product, embedding in zip(products, embeddings):
        point = PointStruct(
            id=product["id"],
            vector=embedding,
            payload={
                "name": product["название"],
                "category": product["категория"],
                "brand": product["бренд"],
                "description": product["описание"],
                "price": product["цена"],
                "specs": product["характеристики"]
            }
        )
        points.append(point)
    
    # Загружаем батчами
    batch_size = 50
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=settings.QDRANT_COLLECTION, points=batch)
    
    print(f"Загружено {len(products)} товаров в Qdrant")


def main():
    """Главная функция для запуска seed."""
    print("Начинаем генерацию каталога...")
    
    # Генерируем данные
    products = generate_products(count_per_category=10)
    print(f"Сгенерировано {len(products)} товаров")
    
    # Загружаем в PostgreSQL
    seed_postgres(products)
    
    # Загружаем в Qdrant
    seed_qdrant(products)
    
    print("Каталог успешно загружен.")


if __name__ == "__main__":
    main()