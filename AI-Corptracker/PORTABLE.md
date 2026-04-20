# AI CorpTracker — переносимый запуск (Docker)

В архиве — исходный код и конфигурация. **Сам Docker в архив не входит**: его нужно один раз установить на компьютер (см. ниже).

## Что нужно на машине

| Компонент | Зачем |
|-----------|--------|
| **Docker Engine** | Контейнеры (PostgreSQL, Kafka, API и т.д.) |
| **Docker Compose** (плагин `docker compose`) | Команда `docker compose up` |

### Установка Docker (кратко)

**Ubuntu / Debian**

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"
# перелогиньтесь, чтобы группа docker подхватилась
```

**Проверка**

```bash
docker --version
docker compose version
```

**Windows** — установите [Docker Desktop](https://www.docker.com/products/docker-desktop/) (лучше с WSL2). Команды выполняйте в **WSL** или в терминале Docker Desktop.

**macOS** — [Docker Desktop](https://www.docker.com/products/docker-desktop/).

---

## Распаковка архива

```bash
tar -xzf AI-Corptracker-portable.tar.gz
cd AI-Corptracker
```

(Если архив в формате `.zip` — распакуйте через проводник или `unzip`.)

---

## Первый запуск

```bash
# 1. Конфигурация (скопировать шаблон)
cp .env.example .env

# 2. Поднять все сервисы
./scripts/docker-up.sh
# или: docker compose up -d

# 3. Дождаться готовности (10–30 сек), затем загрузить демо-данные
docker compose exec api python -m seed.seed_data
```

Если команда `docker compose` не найдена, установите плагин: `sudo apt install docker-compose-plugin`.

---

## Проверка

| Сервис | Адрес |
|--------|--------|
| Swagger API | http://localhost:8000/docs |
| Streamlit | http://localhost:8501 |
| Health | http://localhost:8000/health |

Запуск анализа вручную:

```bash
curl -X POST http://localhost:8000/api/analysis/run
```

---

## Остановка

```bash
cd /путь/к/AI-Corptracker
docker compose down
```

Данные PostgreSQL сохраняются в Docker volume `pgdata`. Чтобы **полностью сбросить БД**:

```bash
docker compose down -v
```

---

## Grafana (если настроена отдельно)

На сервере с установленной Grafana:

```bash
pip install httpx
python3 grafana/provision.py
```

URL и учётные данные задаются в `grafana/provision.py` или переменными окружения — см. `README.md`.

---

## Частые проблемы

| Проблема | Решение |
|----------|---------|
| `permission denied` / docker без sudo | `sudo usermod -aG docker $USER` и перелогин |
| `docker compose` не найден | `sudo apt install docker-compose-plugin` |
| Kafka не стартует | `docker compose down && docker compose up -d` |
| Порт 5432 занят | измените `HOST` порт в `docker-compose.yml` для postgres |

---

## Состав стека в Docker

PostgreSQL, Zookeeper, Kafka, API (FastAPI), Fetcher, Processor, Decision Engine, Streamlit.

Подробнее — `README.md`.
