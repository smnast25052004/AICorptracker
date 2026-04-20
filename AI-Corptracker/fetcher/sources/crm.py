"""
CRM / ERP data source connector.

Fetches customer-related events, deal updates, and pipeline changes.
"""

import random
from datetime import datetime, timedelta
from typing import Generator

from shared.schemas.events import CorporateEvent, EventType
from fetcher.sources.base import BaseSource

CRM_EVENTS = [
    {
        "entity_id": "DEAL-001",
        "title": "Контракт с Banco Nacional (Бразилия)",
        "stage": "negotiation",
        "value": 2_500_000,
        "project": "LATAM",
    },
    {
        "entity_id": "DEAL-002",
        "title": "Лицензия SaaS для Grupo Financiero",
        "stage": "proposal",
        "value": 1_200_000,
        "project": "LATAM",
    },
    {
        "entity_id": "DEAL-003",
        "title": "Обновление CRM Enterprise для Росбанк",
        "stage": "closed_won",
        "value": 800_000,
        "project": "CRM-NEXT",
    },
    {
        "entity_id": "DEAL-004",
        "title": "Контракт на облачную инфраструктуру",
        "stage": "closed_won",
        "value": 3_000_000,
        "project": "INFRA",
    },
    {
        "entity_id": "DEAL-005",
        "title": "Аналитическая платформа для X5 Group",
        "stage": "qualification",
        "value": 1_800_000,
        "project": "DATA-PLATFORM",
    },
]


class CRMSource(BaseSource):

    @property
    def source_name(self) -> str:
        return "crm"

    def fetch_events(self) -> Generator[CorporateEvent, None, None]:
        for deal in CRM_EVENTS:
            yield CorporateEvent(
                event_type=EventType.TASK_UPDATED,
                source_system=self.source_name,
                entity_type="deal",
                entity_id=deal["entity_id"],
                timestamp=datetime.now() - timedelta(days=random.randint(1, 15)),
                payload={
                    "title": deal["title"],
                    "stage": deal["stage"],
                    "value_usd": deal["value"],
                    "project_key": deal["project"],
                    "next_action": random.choice(
                        [
                            "Подготовить коммерческое предложение",
                            "Согласовать условия с юристами",
                            "Назначить техническую демонстрацию",
                            "Ожидание подписи клиента",
                        ]
                    ),
                },
            )

    def health_check(self) -> bool:
        return True
