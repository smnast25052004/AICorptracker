from sqlalchemy import Column, String, Float, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from shared.models.base import Base, TimestampMixin


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.ACTIVE)
    progress = Column(Float, default=0.0)
    lead = Column(String(255))
    goal_id = Column(UUID(as_uuid=True), ForeignKey("strategic_goals.id"))

    goal = relationship("StrategicGoal", back_populates="projects")
    tasks = relationship("Task", back_populates="project")
    documents = relationship("Document", back_populates="project")

    def __repr__(self):
        return f"<Project {self.title[:50]}>"
