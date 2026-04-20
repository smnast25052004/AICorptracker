"""
Notification Engine — generates focused alerts for management.

Produces 1-2 most critical notifications based on risk analysis,
following the requirement to avoid information overload.
"""
import structlog
from dataclasses import dataclass
from sqlalchemy.orm import Session

from shared.models.goal import StrategicGoal, GoalStatus
from shared.models.risk import RiskAssessment

logger = structlog.get_logger()


@dataclass
class Notification:
    level: str  # critical / warning / info
    title: str
    message: str
    goal_title: str
    risk_score: float
    action_required: str


def generate_notifications(db: Session, max_notifications: int = 2) -> list[Notification]:
    """Generate focused notifications for the most critical issues."""

    critical_goals = (
        db.query(StrategicGoal)
        .filter(StrategicGoal.status.in_([GoalStatus.CRITICAL, GoalStatus.AT_RISK]))
        .order_by(StrategicGoal.risk_score.desc())
        .limit(max_notifications)
        .all()
    )

    notifications = []
    for goal in critical_goals:
        latest_risk = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.goal_id == goal.id)
            .order_by(RiskAssessment.created_at.desc())
            .first()
        )

        if goal.status == GoalStatus.CRITICAL:
            level = "critical"
            title = f"КРИТИЧЕСКИЙ РИСК: {goal.title}"
        else:
            level = "warning"
            title = f"Внимание: {goal.title}"

        message = latest_risk.ai_summary if latest_risk else f"Цель «{goal.title}» требует внимания"
        action = "Рекомендуется провести экстренное совещание" if level == "critical" else "Рекомендуется пересмотреть приоритеты"

        notifications.append(Notification(
            level=level,
            title=title,
            message=message,
            goal_title=goal.title,
            risk_score=goal.risk_score,
            action_required=action,
        ))

    return notifications
