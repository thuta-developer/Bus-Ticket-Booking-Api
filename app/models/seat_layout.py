from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SeatLayout(BaseModel):
    __tablename__ = "seat_layouts"

    bus_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Bus ID"
    )

    rows = Column(
        Integer,
        nullable=False,
        comment="Total rows"
    )

    columns = Column(
        Integer,
        nullable=False,
        comment="Total columns per row (seats per row)"
    )

    # Flexible JSON field for custom seat configurations
    config = Column(
        JSON,
        nullable=True,
        comment="Advanced layout config (e.g., aisle positions, skipped seats)"
    )

    # Relationships
    bus = relationship("Bus", back_populates="seat_layout")