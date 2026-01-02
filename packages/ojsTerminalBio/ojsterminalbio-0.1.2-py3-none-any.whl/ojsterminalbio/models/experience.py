"""
Experience Model - Work positions
"""
from sqlalchemy import Column, Integer, String, Boolean

from ..database import Base


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    position = Column(String(255), nullable=True)  # e.g., "Professor"
    organization = Column(String(255), nullable=True)
    department = Column(String(255))
    location = Column(String(255))
    start_date = Column(String(50))  # e.g., "Aug 2023"
    end_date = Column(String(50))  # e.g., "Present" or "Jul 2023"
    is_current = Column(Boolean, default=False)
    description = Column(String(500))
    order = Column(Integer, default=0)
