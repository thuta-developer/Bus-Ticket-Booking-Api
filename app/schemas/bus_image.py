from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class BusImageBase(BaseModel):
    image_url: str = Field(..., max_length=500, description="Image URL")
    order: int = Field(0, ge=0, description="Display order")


class BusImageCreate(BusImageBase):
    bus_id: UUID = Field(..., description="Bus ID")


class BusImageUpdate(BaseModel):
    image_url: Optional[str] = Field(None, max_length=500)
    order: Optional[int] = Field(None, ge=0)


class BusImageResponse(BusImageBase):
    id: UUID
    bus_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True