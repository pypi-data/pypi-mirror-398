"""
Publication Model - Research papers
"""
from sqlalchemy import Column, Integer, String, Text

from ..database import Base


class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(Text)  # Comma-separated authors
    venue = Column(String(255))  # Journal/Conference name
    venue_type = Column(String(50))  # "journal", "conference", "workshop"
    year = Column(Integer, nullable=False)
    month = Column(String(20))
    pages = Column(String(50))
    volume = Column(String(50))
    doi = Column(String(255))
    url = Column(String(500))
    status = Column(String(50), default="published")  # "published", "accepted", "submitted"
    order = Column(Integer, default=0)
