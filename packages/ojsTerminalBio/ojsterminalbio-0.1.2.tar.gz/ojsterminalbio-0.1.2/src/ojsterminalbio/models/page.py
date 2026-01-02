"""
Page Model - Dynamic pages
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from ..database import Base

class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    content = Column(Text)  # HTML content
    is_published = Column(Boolean, default=True)
    show_in_menu = Column(Boolean, default=True)
    menu_order = Column(Integer, default=0)
    meta_description = Column(String(500))
    parent_id = Column(Integer, index=True, nullable=True)  # For nested menus/dropdowns
