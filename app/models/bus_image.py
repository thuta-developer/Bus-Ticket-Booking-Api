from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class BusImage(BaseModel):
    __tablename__ = 'bus_images'

    image_url = Column(
        String(500),
        nullable=False,
        comment="Image URL (Cloudinary or local)"
    )
    order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Order of the image for display purposes"
    )
    bus_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Bus this image belongs to"
    )

    # Relationship
    bus = relationship("Bus", back_populates="images", lazy="selectin")

    def __repr__(self):
        return f"<BusImage {self.image_url[:50]}...>"