"""
Custom Section Item Model - For adding sub-rows/items to a custom section
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

from ..database import Base


class CustomSectionItem(Base):
    __tablename__ = "custom_section_items"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("custom_sections.id"))
    title = Column(String(255), nullable=True)
    subtitle = Column(String(255), nullable=True)
    year = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)
    link = Column(String(255), nullable=True)
    link_text = Column(String(50), nullable=True)
    order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)

    section = relationship("CustomSection", backref=backref("items", cascade="all, delete-orphan", order_by="CustomSectionItem.order"))
