from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel

class BusType(str, enum.Enum):
    VIP = "VIP"
    Standard = "Standard"


class Bus(BaseModel):
    __tablename__ = "buses"

    bus_number = Column(String(50), nullable=False, unique=True, index=True, comment="Bus number (e.g., B-001)")
    capacity = Column(Integer, nullable=False, comment="Total Number of Seats in the Bus")
    bus_type = Column(Enum(BusType), nullable=False, comment="Type of the Bus (e.g., AC, Non-AC, VIP, Express)")
    license_plate = Column(String(20), nullable=False, unique=True, index=True, comment="Vehicle license plate")
    is_active = Column(Boolean, default=True, nullable=False, comment="Indicates if the company is active")

    # ========== Foreign Keys ==========
    company_id = Column(UUID(as_uuid=True), ForeignKey("bus_companies.id", ondelete="CASCADE"), nullable=False, index=True, comment="Company this bus belongs to")

    # ========== Relationships ==========
    company = relationship("BusCompany", back_populates="buses", lazy="selectin")
    schedules = relationship("Schedule", back_populates="bus", cascade="all, delete-orphan")
    seats = relationship("Seat", back_populates="bus", cascade="all, delete-orphan")
    seat_layout = relationship(
        "SeatLayout",
        back_populates="bus",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )


    def __repr__(self):
        return f"<Bus {self.bus_number} ({self.bus_type})>"


    