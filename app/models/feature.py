from sqlalchemy import Column, String, Boolean, Text, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel



bus_features = Table(
    "bus_features",
    BaseModel.metadata,
    Column("bus_id", UUID(as_uuid=True), ForeignKey("buses.id", ondelete="CASCADE"), primary_key=True),
    Column("feature_id", UUID(as_uuid=True), ForeignKey("features.id", ondelete="CASCADE"), primary_key=True)
)




class Feature(BaseModel):
    __tablename__ = "features"

    name = Column(String(100), nullable=False, unique=True, index=True, comment="Feature name")
    icon = Column(String(100), nullable=True, comment="Feature icon (optional)")
    description = Column(Text, nullable=True, comment="Feature description")
    is_active = Column(Boolean, default=True, nullable=False, comment="Indicates if the feature is active")

    buses = relationship("Bus", secondary=bus_features, back_populates="features")

    def __repr__(self):
        return f"<Feature {self.name}>"