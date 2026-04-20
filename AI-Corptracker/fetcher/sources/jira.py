"""
Jira data source connector.

In production, connects to Jira REST API to fetch issues, sprints, and boards.
Currently uses simulated data for demonstration.
"""

import random
from datetime import datetime, timedelta
from typing import Generator

from shared.schemas.events import CorporateEvent, TaskEvent, EventType
from fetcher.sources.base import BaseSource

SIMULATED_PROJECTS = ["LATAM", "CRM-NEXT", "INFRA", "DATA-PLATFORM", "SEC-AUDIT"]

SIMULATED_STATUSES = ["todo", "in_progress", "in_review", "done", "blocked"]

SIMULATED_TASKS = [
    ("Подготовить лицензионное соглашение для LATAM", "LATAM"),
    ("Интеграция платёжного шлюза Mercado Pago", "LATAM"),
    ("Миграция CRM на новую архитектуру", "CRM-NEXT"),
    ("Настройка CI/CD pipeline для нового сервиса", "INFRA"),
    ("Аудит безопасности API-шлюза", "SEC-AUDIT"),
    ("Разработка ETL для аналитического хранилища", "DATA-PLATFORM"),
    ("Перевод документации на португальский", "LATAM"),
    ("Нагрузочное тестирование платформы данных", "DATA-PLATFORM"),
    ("Обновление сертификатов TLS", "INFRA"),
    ("Интеграция SSO для CRM", "CRM-NEXT"),
    ("Разработка API для мобильного приложения LATAM", "LATAM"),
    ("Рефакторинг модуля отчётности", "DATA-PLATFORM"),
    ("Согласование архитектуры с ИБ", "SEC-AUDIT"),
    ("Оптимизация запросов к базе данных CRM", "CRM-NEXT"),
    ("Настройка мониторинга Kubernetes кластера", "INFRA"),
]

ASSIGNEES = [
    "Иванов А.С.",
    "Петрова М.В.",
    "Сидоров К.Н.",
    "Козлова Е.А.",
    "Морозов Д.И.",
    "Волкова А.П.",
]


class JiraSource(BaseSource):

    @property
    def source_name(self) -> str:
        return "jira"

    def fetch_events(self) -> Generator[CorporateEvent, None, None]:
        for i, (title, project) in enumerate(SIMULATED_TASKS):
            status = random.choice(SIMULATED_STATUSES)
            priority = random.choice(["critical", "high", "medium", "low"])
            assignee = random.choice(ASSIGNEES)

            yield TaskEvent(
                event_type=EventType.TASK_CREATED,
                source_system=self.source_name,
                entity_type="task",
                entity_id=f"{project}-{100 + i}",
                timestamp=datetime.now() - timedelta(days=random.randint(1, 30)),
                payload={
                    "title": title,
                    "project_key": project,
                    "status": status,
                    "priority": priority,
                    "assignee": assignee,
                    "story_points": random.choice([1, 2, 3, 5, 8, 13]),
                    "labels": [project.lower()],
                },
                task_title=title,
                task_status=status,
                assignee=assignee,
                project_key=project,
            )

            if status == "blocked":
                yield TaskEvent(
                    event_type=EventType.TASK_BLOCKED,
                    source_system=self.source_name,
                    entity_type="task",
                    entity_id=f"{project}-{100 + i}",
                    timestamp=datetime.now() - timedelta(days=random.randint(0, 5)),
                    payload={
                        "title": title,
                        "blocker_reason": random.choice(
                            [
                                "Ожидание согласования документа",
                                "Зависимость от внешнего подрядчика",
                                "Блокировка из-за смены приоритетов",
                                "Ожидание ресурсов инфраструктуры",
                            ]
                        ),
                    },
                    task_title=title,
                    task_status="blocked",
                    project_key=project,
                )

    def health_check(self) -> bool:
        return True
