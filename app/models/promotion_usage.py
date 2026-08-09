from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel


class UsageStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    CANCELLED = "cancelled"


class PromotionUsage(BaseModel):
    __tablename__ = "promotion_usages"

    status = Column(Enum(UsageStatus), nullable=False, default=UsageStatus.PENDING)
    discount_amount_applied = Column(Float, nullable=False, default=0.0)
    promotion_id = Column(UUID(as_uuid=True), ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False,index=True,comment="Promotion ID")
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who used this promotion"
    )
    booking_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Booking ID (if applicable)"
    )
    promotion = relationship("Promotion", back_populates="usages")
    user = relationship("User", lazy="selectin")
    booking = relationship("Booking", back_populates="promotion_usage")

    def __repr__(self):
        return f"<PromotionUsage {self.promotion_id} by {self.user_id} ({self.status})>"



