from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.models.risk import RiskAssessment
from shared.models.goal import StrategicGoal
from shared.models.recommendation import Recommendation
from shared.schemas.api import RiskResponse, RecommendationResponse

router = APIRouter()


@router.get("/", response_model=list[RiskResponse])
def list_risks(db: Session = Depends(get_db)):
    risks = (
        db.query(RiskAssessment)
        .order_by(RiskAssessment.risk_score.desc())
        .limit(20)
        .all()
    )
    result = []
    for risk in risks:
        goal = db.query(StrategicGoal).filter(StrategicGoal.id == risk.goal_id).first()
        result.append(RiskResponse(
            id=risk.id,
            goal_id=risk.goal_id,
            goal_title=goal.title if goal else "",
            risk_score=risk.risk_score,
            risk_level=risk.risk_level or "medium",
            factors=risk.factors,
            blocked_tasks_count=risk.blocked_tasks_count or 0,
            overdue_tasks_ratio=risk.overdue_tasks_ratio or 0,
            document_delays=risk.document_delays or 0,
            ai_summary=risk.ai_summary,
            created_at=risk.created_at,
        ))
    return result


@router.get("/recommendations", response_model=list[RecommendationResponse])
def list_recommendations(
    goal_id: UUID | None = Query(None, description="Только рекомендации для этой цели"),
    db: Session = Depends(get_db),
):
    q = db.query(Recommendation).order_by(Recommendation.created_at.desc())
    if goal_id is not None:
        q = q.filter(Recommendation.goal_id == goal_id)
    recs = q.limit(50).all()
    result = []
    for rec in recs:
        goal = db.query(StrategicGoal).filter(StrategicGoal.id == rec.goal_id).first()
        result.append(RecommendationResponse(
            id=rec.id,
            goal_id=rec.goal_id,
            goal_title=goal.title if goal else "",
            title=rec.title,
            description=rec.description,
            action=rec.action,
            priority=rec.priority.value if rec.priority else "medium",
            status=rec.status.value if rec.status else "active",
            category=rec.category,
            created_at=rec.created_at,
        ))
    return result
