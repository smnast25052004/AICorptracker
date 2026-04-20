from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared.database import get_db
from decision_engine.engine import run_full_analysis
from decision_engine.notifications import generate_notifications

router = APIRouter()


@router.post("/run")
def trigger_analysis(db: Session = Depends(get_db)):
    """Manually trigger a full analysis cycle."""
    results = run_full_analysis(db)
    return {"status": "completed", "goals_analyzed": len(results), "results": results}


@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    """Get current critical notifications."""
    notifications = generate_notifications(db)
    return {
        "count": len(notifications),
        "notifications": [
            {
                "level": n.level,
                "title": n.title,
                "message": n.message,
                "goal": n.goal_title,
                "risk_score": n.risk_score,
                "action": n.action_required,
            }
            for n in notifications
        ],
    }
