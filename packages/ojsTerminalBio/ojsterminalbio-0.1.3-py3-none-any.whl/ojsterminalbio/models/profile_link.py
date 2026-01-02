"""
Profile Link Model - For dynamic social/external links
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class ProfileLink(Base):
    __tablename__ = "profile_links"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    label = Column(String(50), nullable=False)  # e.g. "Google Scholar", "Twitter"
    url = Column(String(500), nullable=False)
    icon = Column(String(50), nullable=True) # Optional: FontAwesome class or similar
    order = Column(Integer, default=0)
