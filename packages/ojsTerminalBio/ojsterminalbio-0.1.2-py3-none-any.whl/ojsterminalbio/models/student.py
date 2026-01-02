"""
Student Model - PhD and MTech students supervised
"""
from sqlalchemy import Column, Integer, String

from ..database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    program = Column(String(50), nullable=False)  # "PhD", "MTech", "BTech"
    thesis_title = Column(String(500))
    status = Column(String(50))  # "Completed", "Ongoing", "Submitted"
    category = Column(String(50))  # "Regular", "Part Time"
    supervision = Column(String(50))  # "Single", "Joint"
    start_year = Column(String(50))
    end_year = Column(String(50))
    current_position = Column(String(255))  # Where they are now
    order = Column(Integer, default=0)
