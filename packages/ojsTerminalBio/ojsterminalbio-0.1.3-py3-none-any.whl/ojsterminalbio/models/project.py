"""
Project Model - Sponsored and consultancy projects
"""
from sqlalchemy import Column, Integer, String, Boolean, Float

from ..database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    sponsor = Column(String(255))  # e.g., "MeitY", "DST", "ICAR"
    amount = Column(String(100))  # e.g., "₹351.5 Lakh"
    amount_value = Column(Float)  # Numeric value for sorting
    start_date = Column(String(50))
    end_date = Column(String(50))
    is_ongoing = Column(Boolean, default=True)
    role = Column(String(50))  # "PI" or "Co-PI"
    pi_name = Column(String(255))  # Principal Investigator
    co_pi_names = Column(String(500))  # Co-PIs (comma-separated)
    description = Column(String(1000))
    order = Column(Integer, default=0)
