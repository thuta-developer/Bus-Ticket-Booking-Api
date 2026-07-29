from sqlalchemy import Column, String, Boolean, Text,Float,Integer,Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Route(BaseModel):
    __tablename__ = "routes"

    name = Column(String(255), nullable=False, index=True ,comment="Route name (e.g., Yangon - Mandalay)")
    origin = Column(String(255), nullable=False, index=True, comment="Origin City")
    destination = Column(String(255), nullable=False, index=True, comment="Destination City")
    distance = Column(Float, nullable=True, comment="Distance in kilometers")
    duration_minutes = Column(Integer, nullable=True, comment="Estimated duration in minutes")
    base_price = Column(Float, nullable=False, default=0.0, comment="Base price for this route")
    description = Column(Text, nullable=True, comment="Company description")
    is_active = Column(Boolean, default=True, nullable=False)

    # ========== Relationships ==========
    # Schedules နဲ့ ဆက်စပ်မယ် (Phase 8)
    schedules = relationship("Schedule", back_populates="route", cascade="all, delete-orphan")

    # Indexes for better performance
    __table_args__ = (
        Index("ix_routes_origin_destination", "origin", "destination"),
    )

    def __repr__(self):
        return f"<Route {self.origin} -> {self.destination}>"