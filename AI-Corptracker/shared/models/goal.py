from sqlalchemy import Column, String, Float, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from shared.models.base import Base, TimestampMixin


class GoalStatus(str, enum.Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GoalPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StrategicGoal(TimestampMixin, Base):
    __tablename__ = "strategic_goals"

    title = Column(String(500), nullable=False)
    description = Column(Text)
    owner = Column(String(255))
    status = Column(SAEnum(GoalStatus), default=GoalStatus.ON_TRACK)
    priority = Column(SAEnum(GoalPriority), default=GoalPriority.MEDIUM)
    progress = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    target_date = Column(String(50))

    projects = relationship("Project", back_populates="goal")
    risk_assessments = relationship("RiskAssessment", back_populates="goal")
    recommendations = relationship("Recommendation", back_populates="goal")

    def __repr__(self):
        return f"<StrategicGoal {self.title[:50]}>"
