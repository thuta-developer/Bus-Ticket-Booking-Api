from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.schemas.seat_layout import SeatLayoutResponse

class BusTypeEnum(str, Enum):
    VIP = "VIP"
    Standard = "Standard"


class BusBase(BaseModel):
    bus_number: str = Field(..., min_length=1, max_length=50, description="Bus number (e.g., B-001)")
    capacity: int = Field(..., gt=0, description="Total Number of Seats in the Bus")
    bus_type: BusTypeEnum = Field(..., description="Type of the Bus (e.g., AC, Non-AC, VIP, Express)")
    license_plate: str = Field(..., min_length=1, max_length=20, description="Vehicle license plate")
    company_id : UUID = Field(..., description="Company ID")
    is_active: bool = Field(True, description="Indicates if the bus is active")


class BusCreate(BusBase):
    pass

class BusUpdate(BaseModel):
    bus_number: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(None, ge=0, le=100)
    bus_type: Optional[BusTypeEnum] = None
    license_plate: Optional[str] = Field(None, min_length=1, max_length=20)
    company_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class BusResponse(BusBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    company_name: Optional[str] = None
    seat_layout : Optional[SeatLayoutResponse] = None

    class Config:
        from_attributes = True