from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(BaseModel):
    __tablename__ = "bookings"

    # ========== Core Fields ==========
    booking_number = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique booking reference"
    )

    total_amount = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Total amount before discount"
    )

    discount_amount = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Discount applied"
    )

    final_amount = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Final amount after discount"
    )

    status = Column(
        Enum(BookingStatus),
        nullable=False,
        default=BookingStatus.PENDING,
        comment="Booking status"
    )

    # ========== Foreign Keys ==========
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who made the booking"
    )

    schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Schedule ID"
    )

    # ========== Relationships ==========
    user = relationship("User", lazy="selectin")
    schedule = relationship("Schedule", lazy="selectin")
    
    promotion_usage = relationship(
        "PromotionUsage",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Booking {self.booking_number}>"