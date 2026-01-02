"""
Custom Section Model - For adding new arbitrary sections to the profile
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class CustomSection(Base):
    __tablename__ = "custom_sections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text)
    order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    subtitle = Column(String(255), nullable=True)
    year = Column(String(50), nullable=True)
    tags = Column(String(255), nullable=True)
    color = Column(String(50), default="cyan")
    alignment = Column(String(20), default="left")
