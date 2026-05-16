from sqlalchemy import Column, String, Text, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from shared.models.base import Base, TimestampMixin


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    external_id = Column(String(100))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(SAEnum(TaskPriority), default=TaskPriority.MEDIUM)
    source_system = Column(String(50))
    story_points = Column(Integer, default=0)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    assignee = relationship("Employee", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.title[:50]}>"
