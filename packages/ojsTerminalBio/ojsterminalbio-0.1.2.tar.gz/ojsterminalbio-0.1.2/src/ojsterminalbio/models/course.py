"""
Course Model - Courses taught
"""
from sqlalchemy import Column, Integer, String, Boolean

from ..database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    level = Column(String(50))  # "UG", "PG", "UG/PG"
    course_type = Column(String(50))  # "Core", "Elective"
    is_lab = Column(Boolean, default=False)
    description = Column(String(500))
    color = Column(String(50), default="cyan")  # For styling
    order = Column(Integer, default=0)
