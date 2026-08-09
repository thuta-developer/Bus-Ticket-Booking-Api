from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import timezone,datetime

from app.models.base import BaseModel

class PromotionStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"


class Promotion(BaseModel):
    __tablename__ = "promotions"

    name = Column(String(255), nullable=False, index=True, comment="Promotion name")
    description = Column(Text, nullable=True, comment="Promotion description")
    promo_code = Column(String(50), nullable=False, unique=True, index=True, comment="Promotion code")
    discount_percentage = Column(Float, nullable=False, comment="Discount percentage for the promotion")
    discount_amount = Column(Float, nullable=True, comment="Discount amount for the promotion")

    max_usage = Column(Integer, nullable=False, default=1, comment="Maximum number of times the promotion can be used")
    max_usage_per_user = Column(Integer, nullable=False, default=1, comment="Maximum times a single user can use this promotion")

    expires_at = Column(DateTime(timezone=True), nullable=False,comment="Promotion expiration date")
    is_active = Column(Boolean, default=True, nullable=False, comment="Indicates if the promo is active")

    status = Column(Enum(PromotionStatus), nullable=False, default=PromotionStatus.ACTIVE)

    usages = relationship(
        "PromotionUsage",
        back_populates="promotion",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Promotion {self.promo_code} ({self.name})>"

    @property
    def current_usage_count(self) -> int:
        return len(self.usages) if self.usages else 0

    @property
    def is_expired(self) -> bool:
       return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_fully_used(self) -> bool:
        return self.current_usage_count >= self.max_usage





