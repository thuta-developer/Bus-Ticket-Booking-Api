from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class SeatLayoutBase(BaseModel):
    rows: int = Field(..., ge=1, le=50, description="Number of rows")
    columns: int = Field(..., ge=1, le=10, description="Seats per row")
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Custom layout config (e.g., {'aisle_at': 2, 'skip_seats': ['A1']})"
    )


class SeatLayoutCreate(SeatLayoutBase):
    bus_id: UUID = Field(..., description="Bus ID")


class SeatLayoutUpdate(BaseModel):
    rows: Optional[int] = Field(None, ge=1, le=50)
    columns: Optional[int] = Field(None, ge=1, le=10)
    config: Optional[Dict[str, Any]] = None


class SeatLayoutResponse(SeatLayoutBase):
    id: UUID
    bus_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True