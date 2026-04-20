# Список выполненных работ — AI CorpTracker

## 1. Архитектура и инфраструктура
- Спроектирована микросервисная архитектура
- Настроен Docker Compose (PostgreSQL, Kafka, Zookeeper, API, Fetcher, Processor, Decision Engine, Streamlit)
- Добавлено расширение PGVector в PostgreSQL для векторного поиска
- Добавлен init-скрипт `initdb/01_extensions.sql` для автоматического создания расширений

## 2. База данных
- Определены ORM-модели: Employee, StrategicGoal, Project, Task, Document, Event, RiskAssessment, Recommendation
- Добавлена векторная колонка (384 измерения) в модель Document
- Настроена работа с PostgreSQL через SQLAlchemy

## 3. Слой интеграции данных (Fetcher)
- Реализован сервис Fetcher для сбора данных
- Добавлены mock-источники: Jira, Confluence, CRM, Email
- Настроена публикация событий в Kafka (task_updates, document_events, priority_events)
- Добавлен retry при инициализации БД (ожидание схемы от API)

## 4. Потоковая обработка (Kafka)
- Настроены Kafka и Zookeeper
- Реализованы утилиты для producer/consumer в `shared/kafka_utils.py`
- Определены топики для событий

## 5. AI-слой (Processor)
- **Text Analyzer** — извлечение сигналов (блокеры, задержки, риски, прогресс) по regex-паттернам
- **Entity Matcher** — связывание сущностей (цель ↔ проект ↔ задача)
- **Risk Predictor** — взвешенная модель оценки рисков по 5 факторам
- **Embeddings Engine** — генерация эмбеддингов через SentenceTransformer (all-MiniLM-L6-v2)
- **Vector Store** — индексация и семантический поиск через PGVector
- Добавлен retry при инициализации БД

## 6. Decision Engine
- Реализован цикл анализа стратегических целей
- Добавлена генерация рекомендаций и уведомлений
- Добавлен retry при инициализации БД

## 7. REST API
- Реализован FastAPI с эндпоинтами: dashboard/summary, goals, risks, search/semantic, analysis/run, analysis/notifications
- Настроен CORS

## 8. Дашборды Grafana
- Написан скрипт `grafana/provision.py` для настройки источника данных и импорта дашбордов
- Создан дашборд **CEO Overview** — сводка по целям, рискам, рекомендациям
- Создан дашборд **Risk Analysis** — анализ рисков, задачи, документы
- Создан дашборд **Goals Detail** — детали по целям с фильтром
- Исправлены SQL-запросы: enum в UPPERCASE, `::text` для enum, `UPPER(goalpriority)` заменён на `::text`
- Исправлена фильтрация по переменной `$goal`: переход на `multi: true` и `IN ($goal)`

## 9. Интеграция с Grafana
- Подключена внешняя Grafana (http://95.79.92.200:3000)
- Настроен PostgreSQL data source с UID `corptracker-pg`
- Исправлена ошибка «No default database» (database в jsonData)
- Удалён сервис Grafana из docker-compose (конфликт порта 3000)

## 10. Streamlit Dashboard
- Реализован запасной дашборд на Streamlit (Overview, Goals, Risks, Recommendations, Search)

## 11. Seed-данные
- Написан скрипт `seed/seed_data.py` для демо-данных: 5 целей, 11 проектов, 34 задачи, 10 документов, 8 сотрудников

## 12. Пользователи Grafana
- Создан пользователь `viewer` с ролью Viewer для просмотра дашбордов

## 13. Документация
- Обновлён README: архитектура, компоненты, запуск, изменение данных, структура проекта
- Добавлено описание работы AI и примеры использования
