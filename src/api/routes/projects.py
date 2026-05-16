from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.models.project import Project, ProjectStatus
from shared.models.task import Task
from shared.schemas.api import ProjectResponse, ProjectCreate, ProjectUpdate

router = APIRouter()


def _project_to_response(project: Project, db: Session) -> ProjectResponse:
    tasks_count = db.query(Task).filter(Task.project_id == project.id).count()
    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status.value if project.status else "active",
        progress=project.progress or 0,
        lead=project.lead,
        goal_id=project.goal_id,
        created_at=project.created_at,
        tasks_count=tasks_count,
    )


@router.get("/", response_model=list[ProjectResponse])
def list_projects(goal_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Project)
    if goal_id:
        query = query.filter(Project.goal_id == goal_id)
    projects = query.order_by(Project.created_at.desc()).all()
    return [_project_to_response(p, db) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_response(project, db)


@router.post("/", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        title=data.title,
        description=data.description,
        status=ProjectStatus(data.status),
        progress=data.progress,
        lead=data.lead,
        goal_id=data.goal_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_to_response(project, db)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = ProjectStatus(update_data["status"])

    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return _project_to_response(project, db)


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"detail": "Project deleted"}
