from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class BusCompany(BaseModel):
    __tablename__ = "bus_companies"

    name = Column(String(255), nullable=False, unique=True, index=True ,comment="Company name (e.g., JJ Express)")
    description = Column(Text, nullable=True, comment="Company description")

    contact_email = Column(String(255), nullable=True, comment="Contact email address")
    contact_phone = Column(String(20), nullable=True, comment="Contact phone number")
    address = Column(String(255), nullable=True, comment="Company address")

    logo_url = Column(String(255), nullable=True, comment="URL to the company's logo image")
    is_active = Column(Boolean, default=True, nullable=False, comment="Indicates if the company is active")

    # ========== Relationships ==========
    buses = relationship("Bus", back_populates="company", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        
        return f"<BusCompany(name={self.name}, contact_email={self.contact_email}, is_active={self.is_active})>"