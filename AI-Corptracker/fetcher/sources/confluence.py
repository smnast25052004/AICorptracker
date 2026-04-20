"""
Confluence / EDO (Electronic Document Operator) data source connector.

Fetches documents, their statuses, and approval events.
"""

import random
from datetime import datetime, timedelta
from typing import Generator

from shared.schemas.events import CorporateEvent, DocumentEvent, EventType
from fetcher.sources.base import BaseSource

SIMULATED_DOCUMENTS = [
    ("Техническое задание: платёжный шлюз LATAM", "specification", "LATAM"),
    ("Архитектура CRM Next Generation", "specification", "CRM-NEXT"),
    ("Отчёт по аудиту безопасности Q1", "report", "SEC-AUDIT"),
    ("Регуляторные требования рынка LATAM", "report", "LATAM"),
    ("План миграции инфраструктуры", "specification", "INFRA"),
    ("Контракт с поставщиком облачных услуг", "contract", "INFRA"),
    ("Спецификация ETL pipeline", "specification", "DATA-PLATFORM"),
    ("Результаты нагрузочного тестирования", "report", "DATA-PLATFORM"),
    ("Лицензионное соглашение LATAM", "contract", "LATAM"),
    ("Политика безопасности API v2", "specification", "SEC-AUDIT"),
    ("SLA для CRM платформы", "contract", "CRM-NEXT"),
    ("Руководство по развёртыванию K8s", "confluence_page", "INFRA"),
]

AUTHORS = [
    "Иванов А.С.",
    "Петрова М.В.",
    "Сидоров К.Н.",
    "Козлова Е.А.",
    "Морозов Д.И.",
    "Волкова А.П.",
]


class ConfluenceSource(BaseSource):

    @property
    def source_name(self) -> str:
        return "confluence"

    def fetch_events(self) -> Generator[CorporateEvent, None, None]:
        for i, (title, doc_type, project) in enumerate(SIMULATED_DOCUMENTS):
            status = random.choice(["draft", "review", "approved", "rejected"])
            author = random.choice(AUTHORS)

            yield DocumentEvent(
                event_type=EventType.DOCUMENT_CREATED,
                source_system=self.source_name,
                entity_type="document",
                entity_id=f"DOC-{200 + i}",
                timestamp=datetime.now() - timedelta(days=random.randint(5, 60)),
                payload={
                    "title": title,
                    "doc_type": doc_type,
                    "status": status,
                    "author": author,
                    "project_key": project,
                    "content_preview": f"Документ '{title}' описывает ключевые аспекты...",
                },
                doc_title=title,
                doc_status=status,
                author=author,
            )

            if status == "approved":
                yield DocumentEvent(
                    event_type=EventType.DOCUMENT_APPROVED,
                    source_system=self.source_name,
                    entity_type="document",
                    entity_id=f"DOC-{200 + i}",
                    timestamp=datetime.now() - timedelta(days=random.randint(0, 5)),
                    payload={"title": title, "approved_by": random.choice(AUTHORS)},
                    doc_title=title,
                    doc_status="approved",
                )
            elif status == "rejected":
                yield DocumentEvent(
                    event_type=EventType.DOCUMENT_REJECTED,
                    source_system=self.source_name,
                    entity_type="document",
                    entity_id=f"DOC-{200 + i}",
                    timestamp=datetime.now() - timedelta(days=random.randint(0, 3)),
                    payload={
                        "title": title,
                        "rejected_by": random.choice(AUTHORS),
                        "reason": "Требуется доработка раздела безопасности",
                    },
                    doc_title=title,
                    doc_status="rejected",
                )

    def health_check(self) -> bool:
        return True
