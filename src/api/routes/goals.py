from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.models.goal import StrategicGoal, GoalStatus, GoalPriority
from shared.models.project import Project
from shared.models.risk import RiskAssessment
from shared.models.task import Task
from shared.schemas.api import GoalResponse, GoalCreate, GoalUpdate

router = APIRouter()


def _goal_to_response(goal: StrategicGoal, db: Session) -> GoalResponse:
    projects = db.query(Project).filter(Project.goal_id == goal.id).all()
    project_ids = [p.id for p in projects]
    tasks_count = 0
    if project_ids:
        tasks_count = db.query(Task).filter(Task.project_id.in_(project_ids)).count()

    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        owner=goal.owner,
        status=goal.status.value if goal.status else "on_track",
        priority=goal.priority.value if goal.priority else "medium",
        progress=goal.progress or 0,
        risk_score=goal.risk_score or 0,
        target_date=goal.target_date,
        created_at=goal.created_at,
        projects_count=len(projects),
        tasks_count=tasks_count,
    )


@router.get("/", response_model=list[GoalResponse])
def list_goals(db: Session = Depends(get_db)):
    goals = db.query(StrategicGoal).order_by(StrategicGoal.risk_score.desc()).all()
    return [_goal_to_response(g, db) for g in goals]


@router.get("/{goal_id}")
def get_goal(goal_id: str, db: Session = Depends(get_db)):
    goal = db.query(StrategicGoal).filter(StrategicGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    projects = db.query(Project).filter(Project.goal_id == goal.id).all()
    project_ids = [p.id for p in projects]
    tasks = []
    if project_ids:
        tasks = db.query(Task).filter(Task.project_id.in_(project_ids)).all()

    latest_risk = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.goal_id == goal.id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )
    risk_based_reason = None
    if latest_risk:
        risk_based_reason = latest_risk.factors or latest_risk.ai_summary

    status_summary = {
        "todo": "Ожидает начала выполнения",
        "in_progress": "В работе",
        "in_review": "На проверке",
        "done": "Завершена",
    }
    priority_label = {
        "critical": "критический",
        "high": "высокий",
        "medium": "средний",
        "low": "низкий",
    }

    def _task_summary(task: Task) -> str | None:
        description = (task.description or "").strip()
        generic_description = description in {
            f"Задача: {task.title}",
            f"Task: {task.title}",
        }

        if generic_description:
            description = ""

        if task.status and task.status.value == "blocked":
            if description:
                return description
            if risk_based_reason:
                return risk_based_reason
            return "Причина блокировки не указана в данных"

        if description:
            return description

        task_status = task.status.value if task.status else "todo"
        task_priority = priority_label.get(
            task.priority.value if task.priority else "medium", "средний"
        )
        base_status = status_summary.get(task_status, "Статус уточняется")
        return f"{base_status}, приоритет: {task_priority}"

    return {
        "goal": {
            "id": str(goal.id),
            "title": goal.title,
            "description": goal.description,
            "status": goal.status.value if goal.status else "on_track",
            "risk_score": goal.risk_score,
            "progress": goal.progress,
        },
        "projects": [
            {
                "id": str(p.id),
                "title": p.title,
                "status": p.status.value if p.status else "active",
                "progress": p.progress,
            }
            for p in projects
        ],
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "status": t.status.value if t.status else "todo",
                "priority": t.priority.value if t.priority else "medium",
                "summary": _task_summary(t),
            }
            for t in tasks
        ],
    }


@router.post("/", response_model=GoalResponse)
def create_goal(data: GoalCreate, db: Session = Depends(get_db)):
    goal = StrategicGoal(
        title=data.title,
        description=data.description,
        owner=data.owner,
        status=GoalStatus(data.status),
        priority=GoalPriority(data.priority),
        progress=data.progress,
        target_date=data.target_date,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _goal_to_response(goal, db)


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: str, data: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.query(StrategicGoal).filter(StrategicGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = GoalStatus(update_data["status"])
    if "priority" in update_data:
        update_data["priority"] = GoalPriority(update_data["priority"])

    for key, value in update_data.items():
        setattr(goal, key, value)

    db.commit()
    db.refresh(goal)
    return _goal_to_response(goal, db)


@router.delete("/{goal_id}")
def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    goal = db.query(StrategicGoal).filter(StrategicGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"detail": "Goal deleted"}
