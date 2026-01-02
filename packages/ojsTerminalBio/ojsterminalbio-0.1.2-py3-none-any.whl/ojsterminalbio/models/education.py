"""
Education Model - Degrees and qualifications
"""
from sqlalchemy import Column, Integer, String

from ..database import Base


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    degree = Column(String(255), nullable=True)  # e.g., "Ph.D"
    field = Column(String(255))  # e.g., "Computer Science and Engineering"
    institution = Column(String(255), nullable=True)
    location = Column(String(255))
    year = Column(String(50))  # e.g., "2010" or "January 2002"
    description = Column(String(500))  # e.g., "IBM PhD Fellowship Award Recipient"
    order = Column(Integer, default=0)  # For sorting
