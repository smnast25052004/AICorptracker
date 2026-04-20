"""
AI Text Analyzer — extracts signals from corporate text data.

Detects blockers, delays, risks, progress updates, and sentiment
from documents, comments, messages, and task descriptions.
"""
import re
from dataclasses import dataclass
from enum import Enum


class SignalType(str, Enum):
    BLOCKER = "blocker"
    DELAY = "delay"
    RISK = "risk"
    PROGRESS = "progress"
    POSITIVE = "positive"
    ESCALATION = "escalation"


@dataclass
class TextSignal:
    signal_type: SignalType
    confidence: float
    keywords: list[str]
    summary: str


SIGNAL_PATTERNS: dict[SignalType, list[str]] = {
    SignalType.BLOCKER: [
        r"блокир",
        r"заблокирован",
        r"ожидание\s+(?:согласовани|подтвержд|ресурс)",
        r"blocked",
        r"зависимость",
        r"не\s+(?:может|можем|удаётся)",
        r"невозможно",
        r"стоп",
    ],
    SignalType.DELAY: [
        r"задержк",
        r"отложен",
        r"перенос\s+сроков",
        r"просрочен",
        r"опоздание",
        r"не\s+успева",
        r"сдвиг\s+(?:сроков|дат)",
        r"delay",
        r"overdue",
    ],
    SignalType.RISK: [
        r"риск",
        r"угроз",
        r"проблем",
        r"критич",
        r"срочно",
        r"urgent",
        r"critical",
        r"сбой",
        r"отказ",
        r"инцидент",
    ],
    SignalType.PROGRESS: [
        r"завершён",
        r"выполнен",
        r"готов",
        r"запущен",
        r"внедрён",
        r"развёрнут",
        r"completed",
        r"done",
        r"deployed",
    ],
    SignalType.POSITIVE: [
        r"успешн",
        r"отличн",
        r"улучшен",
        r"оптимизирован",
        r"ускорен",
        r"положительн",
    ],
    SignalType.ESCALATION: [
        r"эскалац",
        r"руководств",
        r"смена\s+(?:приоритет|подрядчик|провайдер)",
        r"изменен\s+тариф",
        r"40%",
        r"увеличени\s+стоимост",
    ],
}


class TextAnalyzer:
    """Analyzes text for corporate signals using pattern matching and heuristics."""

    def analyze(self, text: str) -> list[TextSignal]:
        if not text:
            return []

        text_lower = text.lower()
        signals = []

        for signal_type, patterns in SIGNAL_PATTERNS.items():
            matched_keywords = []
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                matched_keywords.extend(matches)

            if matched_keywords:
                confidence = min(0.95, 0.5 + 0.15 * len(matched_keywords))
                signals.append(TextSignal(
                    signal_type=signal_type,
                    confidence=confidence,
                    keywords=list(set(matched_keywords)),
                    summary=self._generate_summary(signal_type, matched_keywords, text),
                ))

        return signals

    def analyze_sentiment(self, text: str) -> tuple[str, float]:
        if not text:
            return "neutral", 0.5

        text_lower = text.lower()
        negative_score = 0
        positive_score = 0

        for pattern in SIGNAL_PATTERNS[SignalType.BLOCKER] + SIGNAL_PATTERNS[SignalType.DELAY] + SIGNAL_PATTERNS[SignalType.RISK]:
            if re.search(pattern, text_lower):
                negative_score += 1

        for pattern in SIGNAL_PATTERNS[SignalType.PROGRESS] + SIGNAL_PATTERNS[SignalType.POSITIVE]:
            if re.search(pattern, text_lower):
                positive_score += 1

        total = negative_score + positive_score
        if total == 0:
            return "neutral", 0.5

        ratio = positive_score / total
        if ratio > 0.6:
            return "positive", ratio
        elif ratio < 0.4:
            return "negative", 1 - ratio
        return "neutral", 0.5

    def _generate_summary(self, signal_type: SignalType, keywords: list[str], original_text: str) -> str:
        type_labels = {
            SignalType.BLOCKER: "Обнаружен блокер",
            SignalType.DELAY: "Обнаружена задержка",
            SignalType.RISK: "Обнаружен риск",
            SignalType.PROGRESS: "Зафиксирован прогресс",
            SignalType.POSITIVE: "Позитивный сигнал",
            SignalType.ESCALATION: "Требуется эскалация",
        }
        preview = original_text[:150].replace("\n", " ")
        return f"{type_labels.get(signal_type, 'Сигнал')}: {preview}..."
