"""
Entity Matcher — links entities across different corporate systems.

Maps tasks to projects, projects to goals, documents to tasks,
even when naming conventions differ between systems.
"""
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class EntityMatch:
    source_entity: str
    target_entity: str
    match_type: str
    confidence: float


PROJECT_TO_GOAL_MAP = {
    "LATAM": "Выход на рынок Латинской Америки",
    "CRM-NEXT": "Модернизация CRM платформы",
    "INFRA": "Обновление IT-инфраструктуры",
    "DATA-PLATFORM": "Создание аналитической платформы данных",
    "SEC-AUDIT": "Обеспечение информационной безопасности",
}

KEYWORD_ASSOCIATIONS = {
    "Выход на рынок Латинской Америки": [
        "latam", "бразил", "латин", "mercado", "лицензи", "fintech",
        "португальск", "banco", "платёжн",
    ],
    "Модернизация CRM платформы": [
        "crm", "клиент", "продаж", "sso", "отчётност", "модерниз",
    ],
    "Обновление IT-инфраструктуры": [
        "infra", "kubernetes", "k8s", "ci/cd", "tls", "облак", "мониторинг",
        "подрядчик", "провайдер",
    ],
    "Создание аналитической платформы данных": [
        "data", "etl", "аналитик", "хранилищ", "pipeline", "нагрузочн",
    ],
    "Обеспечение информационной безопасности": [
        "безопасност", "аудит", "security", "sec", "api-шлюз", "сертификат",
    ],
}


class EntityMatcher:

    def match_project_to_goal(self, project_key: str) -> EntityMatch | None:
        goal_title = PROJECT_TO_GOAL_MAP.get(project_key)
        if goal_title:
            return EntityMatch(
                source_entity=project_key,
                target_entity=goal_title,
                match_type="project_to_goal",
                confidence=1.0,
            )
        return None

    def match_text_to_goal(self, text: str) -> list[EntityMatch]:
        if not text:
            return []

        text_lower = text.lower()
        matches = []

        for goal_title, keywords in KEYWORD_ASSOCIATIONS.items():
            matched = sum(1 for kw in keywords if kw in text_lower)
            if matched > 0:
                confidence = min(0.95, 0.3 + 0.2 * matched)
                matches.append(EntityMatch(
                    source_entity=text[:100],
                    target_entity=goal_title,
                    match_type="text_to_goal",
                    confidence=confidence,
                ))

        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def fuzzy_match(self, text_a: str, text_b: str) -> float:
        return SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio()
