from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from shared.models.base import Base, TimestampMixin


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    department = Column(String(255))
    position = Column(String(255))
    is_active = Column(Boolean, default=True)

    tasks = relationship("Task", back_populates="assignee")

    def __repr__(self):
        return f"<Employee {self.full_name}>"
