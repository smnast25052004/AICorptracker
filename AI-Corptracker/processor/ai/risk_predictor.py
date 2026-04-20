"""
Risk Predictor — evaluates risk levels for strategic goals.

Uses a weighted scoring model based on multiple risk factors:
- Blocked tasks ratio
- Overdue tasks ratio
- Document approval delays
- Negative signals from communications
- Dependencies and external factors
"""

from dataclasses import dataclass, field


@dataclass
class RiskFactor:
    name: str
    value: float
    weight: float
    description: str


@dataclass
class RiskPrediction:
    goal_title: str
    risk_score: float
    risk_level: str
    factors: list[RiskFactor] = field(default_factory=list)
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)


class RiskPredictor:

    RISK_THRESHOLDS = {
        "low": (0.0, 0.3),
        "medium": (0.3, 0.55),
        "high": (0.55, 0.75),
        "critical": (0.75, 1.0),
    }

    def predict(
        self,
        goal_title: str,
        total_tasks: int = 0,
        blocked_tasks: int = 0,
        overdue_tasks: int = 0,
        pending_documents: int = 0,
        rejected_documents: int = 0,
        negative_signals: int = 0,
        positive_signals: int = 0,
        days_to_deadline: int = 90,
        completion_pct: float = 0.0,
    ) -> RiskPrediction:
        factors = []

        blocked_ratio = blocked_tasks / max(total_tasks, 1)
        factors.append(
            RiskFactor(
                name="blocked_tasks",
                value=blocked_ratio,
                weight=0.25,
                description=f"{blocked_tasks} из {total_tasks} задач заблокировано",
            )
        )

        overdue_ratio = overdue_tasks / max(total_tasks, 1)
        factors.append(
            RiskFactor(
                name="overdue_tasks",
                value=overdue_ratio,
                weight=0.20,
                description=f"{overdue_tasks} из {total_tasks} задач просрочено",
            )
        )

        doc_risk = (pending_documents * 0.3 + rejected_documents * 0.7) / max(
            pending_documents + rejected_documents + 1, 1
        )
        factors.append(
            RiskFactor(
                name="document_delays",
                value=doc_risk,
                weight=0.15,
                description=f"Документов на согласовании: {pending_documents}, отклонено: {rejected_documents}",
            )
        )

        total_signals = negative_signals + positive_signals
        signal_ratio = negative_signals / max(total_signals, 1)
        factors.append(
            RiskFactor(
                name="communication_sentiment",
                value=signal_ratio,
                weight=0.15,
                description=f"Негативных сигналов: {negative_signals}, позитивных: {positive_signals}",
            )
        )

        if days_to_deadline > 0:
            expected_progress = max(0, 1.0 - days_to_deadline / 180)
            progress_gap = max(0, expected_progress - completion_pct)
        else:
            progress_gap = max(0, 1.0 - completion_pct)

        factors.append(
            RiskFactor(
                name="progress_gap",
                value=progress_gap,
                weight=0.25,
                description=f"Прогресс: {completion_pct:.0%}, дней до дедлайна: {days_to_deadline}",
            )
        )

        risk_score = sum(f.value * f.weight for f in factors)
        risk_score = min(1.0, max(0.0, risk_score))

        risk_level = "low"
        for level, (low, high) in self.RISK_THRESHOLDS.items():
            if low <= risk_score < high:
                risk_level = level
                break

        summary = self._generate_summary(goal_title, risk_score, risk_level, factors)
        recommendations = self._generate_recommendations(factors, risk_level)

        return RiskPrediction(
            goal_title=goal_title,
            risk_score=risk_score,
            risk_level=risk_level,
            factors=factors,
            summary=summary,
            recommendations=recommendations,
        )

    def _generate_summary(
        self,
        goal_title: str,
        risk_score: float,
        risk_level: str,
        factors: list[RiskFactor],
    ) -> str:
        level_labels = {
            "low": "низкий",
            "medium": "средний",
            "high": "высокий",
            "critical": "критический",
        }
        top_factors = sorted(factors, key=lambda f: f.value * f.weight, reverse=True)[
            :2
        ]
        factor_descriptions = "; ".join(f.description for f in top_factors)

        return (
            f"Цель «{goal_title}»: уровень риска {level_labels[risk_level]} "
            f"({risk_score:.0%}). Основные факторы: {factor_descriptions}."
        )

    def _generate_recommendations(
        self, factors: list[RiskFactor], risk_level: str
    ) -> list[str]:
        recs = []

        for factor in factors:
            if factor.name == "blocked_tasks" and factor.value > 0.2:
                recs.append(
                    "Провести разблокировку задач: выявить причины и назначить ответственных"
                )
            if factor.name == "overdue_tasks" and factor.value > 0.15:
                recs.append(
                    "Пересмотреть приоритеты и перераспределить ресурсы для просроченных задач"
                )
            if factor.name == "document_delays" and factor.value > 0.3:
                recs.append(
                    "Эскалировать согласование документов на уровень руководства"
                )
            if factor.name == "communication_sentiment" and factor.value > 0.5:
                recs.append(
                    "Организовать встречу с командой для обсуждения выявленных проблем"
                )
            if factor.name == "progress_gap" and factor.value > 0.2:
                recs.append(
                    "Скорректировать план и добавить ресурсы для ускорения прогресса"
                )

        if risk_level == "critical":
            recs.insert(0, "СРОЧНО: требуется вмешательство руководства")

        return recs
