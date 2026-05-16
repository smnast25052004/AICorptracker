from sqlalchemy import Column, String, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.models.base import Base, TimestampMixin


class RiskAssessment(TimestampMixin, Base):
    __tablename__ = "risk_assessments"

    goal_id = Column(UUID(as_uuid=True), ForeignKey("strategic_goals.id"))
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20))  # low / medium / high / critical
    factors = Column(Text)
    blocked_tasks_count = Column(Float, default=0)
    overdue_tasks_ratio = Column(Float, default=0.0)
    document_delays = Column(Float, default=0)
    ai_summary = Column(Text)

    goal = relationship("StrategicGoal", back_populates="risk_assessments")

    def __repr__(self):
        return f"<RiskAssessment goal={self.goal_id} score={self.risk_score}>"
