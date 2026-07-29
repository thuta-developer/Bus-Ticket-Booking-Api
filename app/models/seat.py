from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Seat(BaseModel):
    __tablename__ = "seats"

    seat_number = Column(String(50), nullable=False, comment="Seat number (e.g., A-01)")
    row = Column(Integer, nullable=True, comment="Row number (e.g., 1)")
    column = Column(String(10), nullable=True, comment="Column letter (e.g., A)")
    is_available = Column(Boolean, default=True, nullable=False, comment="Indicates if the seat is available")
    is_active = Column(Boolean, default=True, nullable=False,   comment="Is this seat active?")

    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id", ondelete="CASCADE"), nullable=False, index=True)
    bus = relationship("Bus", back_populates="seats", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("bus_id", "seat_number", name="unique_seat_number_per_bus"),
    )

    def __repr__(self):
        return f"<Seat {self.seat_number} (Bus: {self.bus_id})>"