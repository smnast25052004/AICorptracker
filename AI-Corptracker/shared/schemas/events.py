from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
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


class CorporateEvent(BaseModel):
    event_type: EventType
    source_system: str
    entity_type: str
    entity_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskEvent(CorporateEvent):
    task_title: Optional[str] = None
    task_status: Optional[str] = None
    assignee: Optional[str] = None
    project_key: Optional[str] = None


class DocumentEvent(CorporateEvent):
    doc_title: Optional[str] = None
    doc_status: Optional[str] = None
    author: Optional[str] = None
