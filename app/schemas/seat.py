from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class SeatBase(BaseModel):
    seat_number : str = Field(..., min_length=1, max_length=50)
    row : Optional[int] = Field(None, ge=1)
    column : Optional[str] = Field(None, min_length=1, max_length=10)
    is_available : bool = Field(True)
    is_active : bool = Field(True)


class SeatCreate(SeatBase):
    bus_id : UUID = Field(...)

class SeatBatchCreate(BaseModel):
    bus_id : UUID = Field(...)
    start_from : int = Field(..., ge=1)
    count : int = Field(..., ge=1, le=100)

class SeatUpdate(BaseModel):
    seat_number : Optional[str] = Field(None, min_length=1, max_length=50)
    row: Optional[int] = Field(None, ge=1)
    column: Optional[str] = Field(None, max_length=5)
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None


class SeatResponse(SeatBase):
    id : UUID
    bus_id : UUID
    created_at : datetime
    updated_at : datetime
    bus_number : Optional[str] = None

    class Config:
        from_attributes = True