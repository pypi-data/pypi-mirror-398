"""
Award Model - Honors and recognitions
"""
from sqlalchemy import Column, Integer, String

from ..database import Base


class Award(Base):
    __tablename__ = "awards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    year = Column(String(50))
    description = Column(String(500))
    organization = Column(String(255))
    order = Column(Integer, default=0)
