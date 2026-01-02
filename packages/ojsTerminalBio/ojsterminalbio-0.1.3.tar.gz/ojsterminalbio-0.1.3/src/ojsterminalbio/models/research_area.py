"""
Research Area Model - Research interests
"""
from sqlalchemy import Column, Integer, String

from ..database import Base


class ResearchArea(Base):
    __tablename__ = "research_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    color = Column(String(50), default="cyan")  # For styling: cyan, pink, amber
    order = Column(Integer, default=0)
