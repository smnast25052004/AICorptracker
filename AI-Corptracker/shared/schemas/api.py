from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


# --------------- Response schemas ---------------

class GoalResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    owner: Optional[str]
    status: str
    priority: str
    progress: float
    risk_score: float
    target_date: Optional[str]
    created_at: datetime
    projects_count: int = 0
    tasks_count: int = 0

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    progress: float
    lead: Optional[str]
    goal_id: Optional[UUID]
    created_at: datetime
    tasks_count: int = 0

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: UUID
    external_id: Optional[str]
    title: str
    description: Optional[str]
    status: str
    priority: str
    source_system: Optional[str]
    story_points: int = 0
    project_id: Optional[UUID]
    assignee_id: Optional[UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    department: Optional[str]
    position: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: UUID
    external_id: Optional[str]
    title: str
    content: Optional[str]
    doc_type: str
    status: str
    source_system: Optional[str]
    author: Optional[str]
    project_id: Optional[UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskResponse(BaseModel):
    id: UUID
    goal_id: UUID
    goal_title: str = ""
    risk_score: float
    risk_level: str
    factors: Optional[str]
    blocked_tasks_count: float
    overdue_tasks_ratio: float
    document_delays: float
    ai_summary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    id: UUID
    goal_id: UUID
    goal_title: str = ""
    title: str
    description: Optional[str]
    action: Optional[str]
    priority: str
    status: str
    category: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    total_goals: int
    goals_on_track: int
    goals_at_risk: int
    goals_critical: int
    total_projects: int
    total_tasks: int
    blocked_tasks: int
    avg_risk_score: float
    top_risks: list[RiskResponse]
    active_recommendations: list[RecommendationResponse]


# --------------- Create / Update schemas ---------------

class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    status: str = "on_track"
    priority: str = "medium"
    progress: float = 0.0
    target_date: Optional[str] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[float] = None
    target_date: Optional[str] = None


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "active"
    progress: float = 0.0
    lead: Optional[str] = None
    goal_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    lead: Optional[str] = None
    goal_id: Optional[UUID] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    external_id: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    source_system: Optional[str] = None
    story_points: int = 0
    assignee_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    source_system: Optional[str] = None
    story_points: Optional[int] = None
    assignee_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class EmployeeCreate(BaseModel):
    full_name: str
    email: str
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentCreate(BaseModel):
    title: str
    content: Optional[str] = None
    external_id: Optional[str] = None
    doc_type: str = "other"
    status: str = "draft"
    source_system: Optional[str] = "web_upload"
    author: Optional[str] = None
    project_id: Optional[UUID] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None
    status: Optional[str] = None
    author: Optional[str] = None
    project_id: Optional[UUID] = None
