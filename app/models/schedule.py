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

    departure_time = Column(Time(timezone=False), nullable=False, comment="Departure time")
    arrival_time = Column(Time(timezone=False), nullable=False, comment="Arrival time")
    status = Column(Enum(ScheduleStatus), nullable=False, default=ScheduleStatus.ACTIVE)
    is_active = Column(Boolean, default=True, nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id", ondelete="CASCADE"), nullable=False, index=True)

    local_price = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Price for local citizens")
    foreigner_price = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Price for foreigners citizens")

    local_festival_price = Column(Numeric(10, 2), nullable=True, comment="Festival price for locals")
    foreigner_festival_price = Column(Numeric(10, 2), nullable=True, comment="Festival price for foreigners")

    # ==== Booking Window ====
    booking_open_date = Column(DateTime(timezone=True), nullable=False, comment="When booking starts")
    booking_close_date = Column(DateTime(timezone=True), nullable=False, comment="When booking ends")

    # ==== Festival Date Range ====
    festival_start_date = Column(DateTime(timezone=True), nullable=True, comment="Festival period start")
    festival_end_date = Column(DateTime(timezone=True), nullable=True, comment="Festival period end")


    route = relationship("Route", back_populates="schedules", lazy="selectin")
    bus = relationship("Bus", back_populates="schedules", lazy="selectin")

    def __repr__(self):
        return f"<Schedule {self.route.origin} -> {self.route.destination} at {self.departure_time}>"