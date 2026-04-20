"""
Email / messaging data source connector.

Monitors corporate communications for goal-related signals.
"""

import random
from datetime import datetime, timedelta
from typing import Generator

from shared.schemas.events import CorporateEvent, EventType
from fetcher.sources.base import BaseSource

SIMULATED_MESSAGES = [
    {
        "subject": "Re: Задержка лицензирования LATAM",
        "from": "legal@company.com",
        "project": "LATAM",
        "sentiment": "negative",
        "summary": "Юридический отдел сообщает о задержке получения лицензии на 3 недели из-за дополнительных требований регулятора.",
    },
    {
        "subject": "Успешное прохождение аудита безопасности",
        "from": "security@company.com",
        "project": "SEC-AUDIT",
        "sentiment": "positive",
        "summary": "Аудит API-шлюза завершён успешно, все критические замечания устранены.",
    },
    {
        "subject": "Проблемы с производительностью CRM",
        "from": "devops@company.com",
        "project": "CRM-NEXT",
        "sentiment": "negative",
        "summary": "Обнаружены проблемы с производительностью при нагрузке >1000 RPS. Требуется оптимизация.",
    },
    {
        "subject": "Обновление по проекту Data Platform",
        "from": "pm@company.com",
        "project": "DATA-PLATFORM",
        "sentiment": "neutral",
        "summary": "ETL pipeline запущен в staging окружении. Тестирование начнётся на следующей неделе.",
    },
    {
        "subject": "Срочно: смена подрядчика по инфраструктуре",
        "from": "procurement@company.com",
        "project": "INFRA",
        "sentiment": "negative",
        "summary": "Текущий облачный провайдер уведомил об изменении тарифов на 40%. Необходима оценка альтернатив.",
    },
    {
        "subject": "Подтверждение участия в выставке LATAM FinTech",
        "from": "marketing@company.com",
        "project": "LATAM",
        "sentiment": "positive",
        "summary": "Компания подтвердила участие в LATAM FinTech Expo. Необходим работающий демо-стенд к 15 июня.",
    },
]


class EmailSource(BaseSource):

    @property
    def source_name(self) -> str:
        return "email"

    def fetch_events(self) -> Generator[CorporateEvent, None, None]:
        for i, msg in enumerate(SIMULATED_MESSAGES):
            yield CorporateEvent(
                event_type=EventType.COMMENT_ADDED,
                source_system=self.source_name,
                entity_type="message",
                entity_id=f"MSG-{300 + i}",
                timestamp=datetime.now() - timedelta(days=random.randint(0, 10)),
                payload={
                    "subject": msg["subject"],
                    "from": msg["from"],
                    "project_key": msg["project"],
                    "sentiment": msg["sentiment"],
                    "summary": msg["summary"],
                },
            )

    def health_check(self) -> bool:
        return True
