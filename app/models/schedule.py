from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Enum, Numeric, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import time
import enum

from app.models.base import BaseModel


class ScheduleStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    DELAYED = "delayed"


class Schedule(BaseModel):
    __tablename__ = "schedules"

    departure_time = Column(Time, nullable=False)
    arrival_time = Column(Time, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(ScheduleStatus), nullable=False, default=ScheduleStatus.ACTIVE)

    is_active = Column(Boolean, default=True, nullable=False)

    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id", ondelete="CASCADE"), nullable=False, index=True)

    route = relationship("Route", back_populates="schedules", lazy="selectin")
    bus = relationship("Bus", back_populates="schedules", lazy="selectin")

    def __repr__(self):
        return f"<Schedule {self.route.origin} -> {self.route.destination} at {self.departure_time}>"
