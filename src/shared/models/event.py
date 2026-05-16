from sqlalchemy import Column, String, Text, Enum as SAEnum, JSON
import enum

from shared.models.base import Base, TimestampMixin


class EventType(str, enum.Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_BLOCKED = "task_blocked"
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_APPROVED = "document_approved"
    DOCUMENT_REJECTED = "document_rejected"
    PRIORITY_CHANGED = "priority_changed"
    GOAL_PROGRESS_UPDATED = "goal_progress_updated"
    RISK_DETECTED = "risk_detected"
    COMMENT_ADDED = "comment_added"


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    event_type = Column(SAEnum(EventType), nullable=False)
    source_system = Column(String(50))
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    payload = Column(JSON)
    processed = Column(String(20), default="pending")

    def __repr__(self):
        return f"<Event {self.event_type} from {self.source_system}>"
