from sqlalchemy import Column, String, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

from shared.models.base import Base, TimestampMixin


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class DocumentType(str, enum.Enum):
    SPECIFICATION = "specification"
    CONTRACT = "contract"
    REPORT = "report"
    CONFLUENCE_PAGE = "confluence_page"
    EMAIL = "email"
    OTHER = "other"


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    external_id = Column(String(100))
    title = Column(String(500), nullable=False)
    content = Column(Text)
    doc_type = Column(SAEnum(DocumentType), default=DocumentType.OTHER)
    status = Column(SAEnum(DocumentStatus), default=DocumentStatus.DRAFT)
    source_system = Column(String(50))
    author = Column(String(255))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    embedding = Column(Vector(384), nullable=True)

    project = relationship("Project", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.title[:50]}>"
