# AI CorpTracker

**AI-система стратегического мониторинга корпоративных целей**

Система собирает данные из корпоративных инструментов (Jira, Confluence, CRM, почта), анализирует их с помощью AI и показывает руководству состояние стратегических целей, риски и рекомендации на дашборде Grafana.

**Перенос на другую машину:** соберите архив `bash scripts/package-portable.sh` → файл `dist/AI-Corptracker-portable.tar.gz`, затем следуйте [PORTABLE.md](PORTABLE.md).

---

## Как устроена система

```
  Jira / Confluence / CRM / Почта          ← откуда берём данные
                  │
                  ▼
            ┌──────────┐
            │ Fetcher  │  Забирает события из систем
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │  Kafka   │  Очередь событий (task_updates, document_events...)
            └────┬─────┘
                 │
                 ▼
          ┌──────────────┐
          │ AI Processor │  Анализирует текст, ищет риски, создаёт эмбеддинги
          └──────┬───────┘
                 │
          ┌──────┴───────┐
          ▼              ▼
   ┌────────────┐  ┌────────────┐
   │ PostgreSQL │  │  PGVector  │   Хранилище данных + векторный поиск
   └──────┬─────┘  └──────┬─────┘
          └───────┬───────┘
                  ▼
        ┌──────────────────┐
        │ Decision Engine  │  Считает риски по целям, генерирует рекомендации
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │     Grafana      │  Дашборды для CEO
        └──────────────────┘
```

---

## Что делает каждый компонент

### Fetcher — сборщик данных
Подключается к корпоративным системам, забирает события и отправляет их в Kafka.

**Откуда берёт данные:**
- Jira — задачи, статусы, блокеры
- Confluence / ЭДО — документы, согласования
- CRM — сделки, контракты
- Почта — письма, уведомления

**Что генерирует:** события вида `TaskCreated`, `TaskUpdated`, `DocumentApproved`, `PriorityChanged`

> Сейчас работает с моковыми (демонстрационными) источниками. Для подключения реальных систем нужно реализовать коннекторы в `fetcher/sources/`.

### Kafka — очередь событий
Принимает события от Fetcher и передаёт их в AI Processor. Топики:
- `task_updates` — изменения задач
- `document_events` — события по документам
- `priority_events` — смена приоритетов

### AI Processor — мозг системы
Читает события из Kafka и прогоняет через AI-конвейер:

| Модуль | Что делает | Как работает |
|--------|-----------|--------------|
| **Text Analyzer** | Находит в тексте сигналы: блокеры, задержки, риски, прогресс | Regex-паттерны (рус + англ) |
| **Entity Matcher** | Связывает задачу → проект → цель, даже если названия разные | Fuzzy matching + ключевые слова |
| **Embeddings Engine** | Превращает текст в числовой вектор (384 числа) для поиска по смыслу | Нейросеть `all-MiniLM-L6-v2` |
| **Risk Predictor** | Оценивает вероятность срыва цели (0–100%) | Взвешенная скоринговая модель |

### PostgreSQL + PGVector — хранилище
Одна база данных, два назначения:
- **PostgreSQL** — структурированные данные: цели, проекты, задачи, документы, сотрудники, оценки рисков, рекомендации
- **PGVector** — расширение для векторного поиска. Хранит эмбеддинги документов и позволяет искать по смыслу (например, запрос «проблемы с лицензией» найдёт документ «Задержка разрешений LATAM»)

### Decision Engine — система решений
Периодически анализирует каждую стратегическую цель и формирует:
- **Risk score** — оценка риска по 5 факторам (блокеры, просрочки, задержки документов, тональность коммуникаций, отставание от плана)
- **Рекомендации** — конкретные действия для руководства
- **Уведомления** — только самое критичное, 1–2 пункта без перегрузки информацией

### API — интерфейс доступа к данным
REST API на FastAPI. Через него Grafana и Streamlit получают данные.

| Эндпоинт | Что отдаёт |
|----------|-----------|
| `GET /api/dashboard/summary` | Сводка: сколько целей, рисков, рекомендаций |
| `GET /api/goals/` | Все стратегические цели |
| `GET /api/goals/{id}` | Одна цель + проекты + задачи |
| `GET /api/risks/` | Топ рисков |
| `GET /api/risks/recommendations` | Рекомендации AI |
| `GET /api/search/semantic?q=текст` | Семантический поиск по документам |
| `POST /api/analysis/run` | Запуск AI-анализа вручную |
| `GET /api/analysis/notifications` | Критические уведомления |

Swagger-документация: http://localhost:8000/docs

### Grafana — дашборды для CEO
Три дашборда, подключены напрямую к PostgreSQL:

| Дашборд | Что показывает |
|---------|---------------|
| **CEO Overview** | Здоровье целей (🟢🟡🔴), ключевые метрики, рекомендации |
| **Risk Analysis** | Факторы рисков, заблокированные задачи, задержки документов |
| **Goals Detail** | Детали по выбранной цели: задачи, нагрузка, документы |

---

## Нейросеть

Используется **all-MiniLM-L6-v2** — компактная модель от Microsoft (22 млн параметров). Работает локально, без внешних API.

Что делает: превращает текст в вектор из 384 чисел. Похожие по смыслу тексты получают похожие векторы, что позволяет искать документы по смыслу, а не по точному совпадению слов.

---

## Как запустить

### 1. Настроить окружение

```bash
cp .env.example .env
```

### 2. Поднять все сервисы

```bash
docker-compose up -d
```

Запустятся: PostgreSQL, Kafka, Zookeeper, API, Fetcher, Processor, Decision Engine, Streamlit.

### 3. Загрузить демо-данные

```bash
docker-compose exec api python -m seed.seed_data
```

Создаст: 5 целей, 11 проектов, 34 задачи, 10 документов, 8 сотрудников.

### 4. Запустить AI-анализ

```bash
curl -X POST http://localhost:8000/api/analysis/run
```

### 5. Настроить Grafana-дашборды

```bash
python3 grafana/provision.py
```

Скрипт создаст источник данных PostgreSQL и импортирует 3 дашборда.

Если в БД используются **ENUM** в верхнем регистре (`ON_TRACK`, `DONE`, …), а в панелях пусто — привёлите SQL в JSON: `python3 grafana/fix_dashboard_enums.py`, затем снова `python3 grafana/provision.py`.

Поднять все контейнеры (если нет `docker-compose` в `/usr/bin`, скрипт попробует `docker compose`, PATH и `/usr/local/bin`):

```bash
./scripts/docker-up.sh
```

Первый запуск долго собирает образ (в т.ч. PyTorch). Дальше — быстрее.

---

## Как менять данные

### Через SQL напрямую

```bash
docker-compose exec postgres psql -U corptracker -d corptracker
```

```sql
-- Посмотреть цели
SELECT title, status, risk_score, progress FROM strategic_goals;

-- Изменить статус
UPDATE strategic_goals SET status = 'CRITICAL' WHERE title LIKE '%CRM%';

-- Добавить цель
INSERT INTO strategic_goals (title, description, owner, priority, status, progress, risk_score, target_date)
VALUES ('Новая цель', 'Описание', 'CEO', 'HIGH', 'ON_TRACK', 0, 0.1, '2026-12-31');
```

### Через seed-скрипт

Отредактировать `seed/seed_data.py` и перезапустить:

```bash
docker-compose exec postgres psql -U corptracker -d corptracker -c \
  "TRUNCATE strategic_goals, projects, tasks, documents, employees, risk_assessments, recommendations CASCADE;"
docker-compose exec api python -m seed.seed_data
```

---

## Структура проекта

```
AI-Corptracker/
├── api/                    # REST API (FastAPI)
│   ├── main.py             # Точка входа, подключение роутеров
│   └── routes/             # Эндпоинты: goals, risks, dashboard, search, analysis
├── fetcher/                # Сборщик данных
│   ├── main.py             # Основной цикл опроса источников
│   └── sources/            # Коннекторы: Jira, Confluence, CRM, Email (моки)
├── processor/              # AI-обработка событий
│   ├── main.py             # Kafka-consumer + AI-конвейер
│   ├── vector_store.py     # Индексация и поиск по PGVector
│   └── ai/                 # AI-модули
│       ├── text_analyzer.py    # Извлечение сигналов из текста
│       ├── entity_matcher.py   # Связывание сущностей
│       ├── embeddings.py       # Генерация векторных эмбеддингов
│       └── risk_predictor.py   # Прогноз рисков
├── decision_engine/        # Система решений
│   ├── main.py             # Периодический цикл анализа
│   ├── engine.py           # Агрегация данных + расчёт рисков
│   └── notifications.py    # Генерация уведомлений
├── shared/                 # Общий код для всех сервисов
│   ├── config.py           # Конфигурация из .env
│   ├── database.py         # Подключение к PostgreSQL
│   ├── kafka_utils.py      # Работа с Kafka
│   ├── models/             # ORM-модели (SQLAlchemy)
│   └── schemas/            # Pydantic-схемы для API и Kafka
├── dashboard/              # Streamlit-дашборд (запасной)
├── grafana/                # Grafana-дашборды
│   ├── provision.py        # Скрипт автоматической настройки
│   ├── fix_dashboard_enums.py  # Приведение SQL к меткам PostgreSQL ENUM
│   └── dashboards/         # JSON-файлы 3 дашбордов
├── seed/                   # Скрипт загрузки демо-данных
├── docker-compose.yml      # Все сервисы
├── Dockerfile              # Образ Python-приложения
└── .env.example            # Шаблон переменных окружения
```

---

## Пример работы AI

**Цель:** «Выход на рынок Латинской Америки»

1. **Fetcher** обнаруживает заблокированную задачу в Jira: «Подготовить документы для регулятора Бразилии»
2. **AI Processor** анализирует текст → сигнал `BLOCKER`, уверенность 85%
3. **Entity Matcher** связывает: задача → проект «Лицензирование LATAM» → цель «Выход на рынок LATAM»
4. **Email-коннектор** находит письмо: «Задержка лицензирования на 3 недели»
5. **Risk Predictor** считает: **риск = 78%** (критический)
6. **Decision Engine** генерирует:
   - Уведомление: «КРИТИЧЕСКИЙ РИСК: Выход на рынок LATAM»
   - Рекомендация: «Эскалировать согласование на уровень руководства»
7. **Grafana** показывает цель красным (🔴) с рекомендацией

---

## Доступы

| Что | Адрес |
|-----|-------|
| Grafana | http://95.79.92.200:3000 |
| API Swagger | http://localhost:8000/docs |
| Streamlit | http://localhost:8501 |
