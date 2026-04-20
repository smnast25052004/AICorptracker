from sqlalchemy import Column, String, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from shared.models.base import Base, TimestampMixin


class RecommendationPriority(str, enum.Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    IMPLEMENTED = "implemented"
    DISMISSED = "dismissed"


class Recommendation(TimestampMixin, Base):
    __tablename__ = "recommendations"

    goal_id = Column(UUID(as_uuid=True), ForeignKey("strategic_goals.id"))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    action = Column(Text)
    priority = Column(SAEnum(RecommendationPriority), default=RecommendationPriority.MEDIUM)
    status = Column(SAEnum(RecommendationStatus), default=RecommendationStatus.ACTIVE)
    category = Column(String(100))

    goal = relationship("StrategicGoal", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation {self.title[:50]}>"
