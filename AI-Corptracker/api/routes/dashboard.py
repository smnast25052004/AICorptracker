from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from shared.database import get_db
from shared.models.goal import StrategicGoal, GoalStatus
from shared.models.project import Project
from shared.models.task import Task, TaskStatus
from shared.models.risk import RiskAssessment
from shared.models.recommendation import Recommendation, RecommendationStatus
from shared.schemas.api import DashboardSummary, RiskResponse, RecommendationResponse

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    goals = db.query(StrategicGoal).all()
    total_goals = len(goals)
    goals_on_track = sum(1 for g in goals if g.status == GoalStatus.ON_TRACK)
    goals_at_risk = sum(1 for g in goals if g.status == GoalStatus.AT_RISK)
    goals_critical = sum(1 for g in goals if g.status == GoalStatus.CRITICAL)

    total_projects = db.query(Project).count()
    total_tasks = db.query(Task).count()
    blocked_tasks = db.query(Task).filter(Task.status == TaskStatus.BLOCKED).count()

    avg_risk = db.query(func.avg(StrategicGoal.risk_score)).scalar() or 0.0

    top_risks_raw = (
        db.query(RiskAssessment)
        .order_by(RiskAssessment.risk_score.desc())
        .limit(5)
        .all()
    )
    top_risks = []
    for risk in top_risks_raw:
        goal = db.query(StrategicGoal).filter(StrategicGoal.id == risk.goal_id).first()
        top_risks.append(
            RiskResponse(
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
            )
        )

    active_recs_raw = (
        db.query(Recommendation)
        .filter(Recommendation.status == RecommendationStatus.ACTIVE)
        .order_by(Recommendation.created_at.desc())
        .limit(10)
        .all()
    )
    active_recs = []
    for rec in active_recs_raw:
        goal = db.query(StrategicGoal).filter(StrategicGoal.id == rec.goal_id).first()
        active_recs.append(
            RecommendationResponse(
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
            )
        )

    return DashboardSummary(
        total_goals=total_goals,
        goals_on_track=goals_on_track,
        goals_at_risk=goals_at_risk,
        goals_critical=goals_critical,
        total_projects=total_projects,
        total_tasks=total_tasks,
        blocked_tasks=blocked_tasks,
        avg_risk_score=float(avg_risk),
        top_risks=top_risks,
        active_recommendations=active_recs,
    )
