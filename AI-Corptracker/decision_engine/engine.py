"""
Decision Engine — generates risk assessments and recommendations for strategic goals.

Aggregates data from all sources, runs the risk prediction model,
and produces actionable insights for management.
"""
import structlog
from sqlalchemy.orm import Session

from shared.models.goal import StrategicGoal, GoalStatus
from shared.models.project import Project
from shared.models.task import Task, TaskStatus
from shared.models.document import Document, DocumentStatus
from shared.models.risk import RiskAssessment
from shared.models.recommendation import Recommendation, RecommendationPriority, RecommendationStatus
from shared.models.event import Event
from processor.ai.risk_predictor import RiskPredictor
from processor.ai.text_analyzer import TextAnalyzer, SignalType

logger = structlog.get_logger()

risk_predictor = RiskPredictor()
text_analyzer = TextAnalyzer()


def analyze_goal(db: Session, goal: StrategicGoal) -> dict:
    """Run full analysis pipeline for a strategic goal."""

    projects = db.query(Project).filter(Project.goal_id == goal.id).all()
    project_ids = [p.id for p in projects]

    tasks = []
    if project_ids:
        tasks = db.query(Task).filter(Task.project_id.in_(project_ids)).all()

    documents = []
    if project_ids:
        documents = db.query(Document).filter(Document.project_id.in_(project_ids)).all()

    total_tasks = len(tasks)
    blocked_tasks = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
    done_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE)
    pending_docs = sum(1 for d in documents if d.status in [DocumentStatus.DRAFT, DocumentStatus.REVIEW])
    rejected_docs = sum(1 for d in documents if d.status == DocumentStatus.REJECTED)

    negative_signals = 0
    positive_signals = 0
    recent_events = (
        db.query(Event)
        .filter(Event.entity_type.in_(["task", "document", "message"]))
        .order_by(Event.created_at.desc())
        .limit(50)
        .all()
    )

    for event in recent_events:
        if event.payload:
            text_content = str(event.payload)
            signals = text_analyzer.analyze(text_content)
            for signal in signals:
                if signal.signal_type in [SignalType.BLOCKER, SignalType.DELAY, SignalType.RISK]:
                    negative_signals += 1
                elif signal.signal_type in [SignalType.PROGRESS, SignalType.POSITIVE]:
                    positive_signals += 1

    completion_pct = done_tasks / max(total_tasks, 1)

    prediction = risk_predictor.predict(
        goal_title=goal.title,
        total_tasks=total_tasks,
        blocked_tasks=blocked_tasks,
        overdue_tasks=max(0, total_tasks - done_tasks - blocked_tasks) // 3,
        pending_documents=pending_docs,
        rejected_documents=rejected_docs,
        negative_signals=negative_signals,
        positive_signals=positive_signals,
        days_to_deadline=90,
        completion_pct=completion_pct,
    )

    risk_assessment = RiskAssessment(
        goal_id=goal.id,
        risk_score=prediction.risk_score,
        risk_level=prediction.risk_level,
        factors="; ".join(f.description for f in prediction.factors),
        blocked_tasks_count=blocked_tasks,
        overdue_tasks_ratio=1 - completion_pct,
        document_delays=pending_docs + rejected_docs,
        ai_summary=prediction.summary,
    )
    db.add(risk_assessment)

    status_map = {
        "low": GoalStatus.ON_TRACK,
        "medium": GoalStatus.AT_RISK,
        "high": GoalStatus.AT_RISK,
        "critical": GoalStatus.CRITICAL,
    }
    goal.status = status_map.get(prediction.risk_level, GoalStatus.ON_TRACK)
    goal.risk_score = prediction.risk_score
    goal.progress = completion_pct * 100

    for rec_text in prediction.recommendations:
        priority_map = {
            "critical": RecommendationPriority.URGENT,
            "high": RecommendationPriority.HIGH,
        }
        rec = Recommendation(
            goal_id=goal.id,
            title=rec_text[:200],
            description=prediction.summary,
            action=rec_text,
            priority=priority_map.get(prediction.risk_level, RecommendationPriority.MEDIUM),
            status=RecommendationStatus.ACTIVE,
            category="risk_mitigation",
        )
        db.add(rec)

    db.commit()

    return {
        "goal": goal.title,
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "summary": prediction.summary,
        "recommendations_count": len(prediction.recommendations),
    }


def run_full_analysis(db: Session) -> list[dict]:
    """Run analysis for all active strategic goals."""
    goals = db.query(StrategicGoal).all()
    results = []

    for goal in goals:
        try:
            result = analyze_goal(db, goal)
            results.append(result)
            logger.info("Goal analyzed", goal=goal.title[:50], risk=result["risk_score"])
        except Exception as e:
            logger.error("Goal analysis failed", goal=goal.title[:50], error=str(e))

    return results
