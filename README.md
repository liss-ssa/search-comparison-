## Загрузка данных

После запуска контейнеров загрузите каталог товаров:

```bash
# Через API endpoint
curl -X POST http://localhost:8000/seed

# Или через docker exec
docker compose exec backend python -m app.utils.seed_data
```

# Search Comparison: BM25 vs Vector Search

Сравнения эффективности лексического (BM25) и семантического (Vector) поиска в RAG-системе для каталога косметики и бытовой химии.

## Цель

Сравнить два подхода к поиску и оценить, какой из них лучше возвращает релевантные результаты для различных типов запросов:
- **BM25** (PostgreSQL `tsvector`) — лексический поиск по точному совпадению слов
- **Vector** (Qdrant + `bge-m3`) — семантический поиск по эмбеддингам

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  PostgreSQL  │     │   Qdrant    │
│  (Backend)  │     │   (BM25)     │     │  (Vector)   │
└─────────────┘     └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Ollama    │────▶│  LLM Answer  │
│ (Embed+LLM) │     │  Generation  │
└─────────────┘     └──────────────┘
```

### Стек технологий
- **Backend**: FastAPI + Pydantic (Python 3.11)
- **BM25 поиск**: PostgreSQL 16 + `tsvector` + русский стеммер
- **Vector поиск**: Qdrant v1.11.0 + модель `bge-m3` (1024-мерные эмбеддинги)
- **LLM**: Ollama + `llama3.1:latest`
- **Контейнеризация**: Docker Compose

## Структура проекта

```
search-comparison/
├── docker-compose.yml          # Оркестрация контейнеров
├── .env.example                # Шаблон переменных окружения
├── .gitignore
├── README.md
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py             # FastAPI endpoints
        ├── config.py           # Pydantic Settings
        ├── database/
        │   ├── postgres.py     # Инициализация PostgreSQL
        │   └── qdrant.py       # Инициализация Qdrant
        ├── search/
        │   ├── bm25.py         # Лексический поиск
        │   ├── vector.py       # Семантический поиск
        │   └── hybrid.py       # Комбинированный поиск
        ├── llm/
        │   └── ollama_client.py # Генерация ответов
        ├── models/
        │   └── schemas.py      # Pydantic схемы
        └── utils/
            └── seed_data.py    # Генерация каталога (~90 товаров)
```

## Быстрый старт

### 1. Клонировать и настроить

```bash
git clone <your-repo-url>
cd pract
cp .env.example .env
```

### 2. Запустить контейнеры

```bash
docker compose up --build -d
```

### 3. Скачать модели (один раз)

```bash
docker compose exec ollama ollama pull bge-m3
docker compose exec ollama ollama pull llama3.1:latest
```

### 4. Загрузить каталог товаров

```bash
curl.exe -X POST http://localhost:8000/seed
```

### 5. Открыть Swagger UI

http://localhost:8000/docs

## API Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/health` | GET | Проверка здоровья сервиса |
| `/seed` | POST | Генерация и загрузка каталога |
| `/search/bm25` | POST | Лексический поиск |
| `/search/vector` | POST | Семантический поиск |
| `/compare` | POST | Сравнение обоих методов |
| `/ask` | POST | RAG-ответ на вопрос |

## Примеры запросов

### Сравнение BM25 vs Vector

```bash
# Брендовый запрос (побеждает BM25)
curl.exe -X POST http://localhost:8000/compare -H "Content-Type: application/json" -d "{\"query\": \"La Roche-Posay\", \"limit\": 5}"

# Семантический запрос (побеждает Vector)
curl.exe -X POST http://localhost:8000/compare -H "Content-Type: application/json" -d "{\"query\": \"чем помазать лицо от прыщей\", \"limit\": 5}"

# Разговорный запрос (побеждает Vector)
curl.exe -X POST http://localhost:8000/compare -H "Content-Type: application/json" -d "{\"query\": \"кожа шелушится и стягивается\", \"limit\": 5}"
```

### RAG-ответ

```bash
curl.exe -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"посоветуй шампунь для сухих волос\", \"top_k\": 5}"
```

## Результаты сравнения

| Критерий | BM25 | Vector (bge-m3) |
|----------|------|-----------------|
| Точные запросы (бренды) | Отлично | Хорошо  |
| Семантические запросы | Средне | Отлично |
| Синонимы | Не находит | Находит |
| Разговорный язык | Плохо | Хорошо |
| Скорость | 0.01 сек | 0.2-0.4 сек |

### Вывод

- **BM25** — король точных запросов (бренды, артикулы, категории)
- **Vector** — король семантических запросов (описание проблем, синонимы)
- **Для production** рекомендуется гибридный подход

## Остановка проекта

```bash
docker compose down              # Остановить контейнеры
docker compose down -v           # Остановить + удалить volumes
```
