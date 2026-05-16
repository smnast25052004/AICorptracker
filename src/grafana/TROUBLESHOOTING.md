# Grafana — диагностика «нет данных» / пустые панели

## Что проверить

1. **Два экземпляра Grafana**
   - **Системная** (apt, systemd): порт **3000** — то, что открыто снаружи по `95.79.92.200:3000`.
   - **Docker** (`docker-compose`): порт **3001** → контейнер Grafana 11.x с provisioning из репозитория.
   - Убедитесь, что смотрите нужный URL и что источник данных в **Connections → Data sources** ведёт на живой PostgreSQL (для системной Grafana: `127.0.0.1:5432` или IP хоста, **не** имя `postgres` — оно резолвится только внутри Docker-сети).

2. **Источник данных**
   - **Save & test** для `CorpTracker PostgreSQL` должен быть зелёным.
   - Пересоздать источник и импорт дашбордов с сервера:
     ```bash
     cd /path/to/AI-Corptracker
     python3 grafana/provision.py --recreate-datasource
     ```

3. **«You do not currently have a default database configured» (Grafana 12+)**
   - Имя БД должно быть не только в поле **Database** у источника, но и в **`jsonData.database`** (баг/изменение плагина `grafana-postgresql-datasource`).
   - Исправление: обновить `grafana/provisioning/datasources/datasource.yml` и перезапустить контейнер Grafana **или** выполнить `python3 grafana/provision.py` (скрипт сам допишет `jsonData.database` существующему источнику).

4. **Grafana 12 + PostgreSQL (пустые панели)**
   - В логах `journalctl -u grafana-server` при ошибке запросов часто встречается `POST /api/ds/query` с **400** и текстом вроде **«Unrecognized query model format»** — у запроса панели не задан **`format`** (`table` / `time_series`). После правки панели в UI или повторного импорта JSON из репозитория проблема уходит.

5. **Данные в БД**
   - Дашборды читают таблицы `strategic_goals`, `tasks`, `projects` и т.д. Если пайплайн (fetcher/processor) не пишет в БД, панели будут с нулями — это не ошибка Grafana.

6. **Дашборд «Goals Detail» и переменная «Все цели»**
   - В запросах используется подстановка **`${goal:sqlstring}`** для `IN (...)`, чтобы корректно работали multi-select и режим «All» в Grafana 12.

7. **Часть панелей пустая / «No data» при рабочем подключении**
   - В PostgreSQL статусы и приоритеты заданы **ENUM** с метками в **ВЕРХНЕМ РЕГИСТРЕ** (`ON_TRACK`, `DONE`, `DRAFT`, …). В SQL дашбордов должны использоваться те же строки, иначе сравнение не срабатывает или запрос падает.
   - Исключение: поле **`risk_assessments.risk_level`** — обычный `VARCHAR`, в данных часто **нижний регистр** (`low`, `medium`); для этих панелей в JSON оставлен `CASE ra.risk_level WHEN 'low' ...` без приведения к enum.
   - После изменения схемы БД перегенерируйте SQL или выполните **`python3 grafana/fix_dashboard_enums.py`**, затем **`python3 grafana/provision.py`**.

## Логи

```bash
journalctl -u grafana-server -n 100 --no-pager | grep -E 'ds/query|error|postgres'
```

В браузере: панель → **Inspect** → **Query** — там текст ошибки от источника данных.
