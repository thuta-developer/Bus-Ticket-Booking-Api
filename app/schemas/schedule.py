from typing import Optional
from uuid import UUID
from datetime import datetime, time
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from enum import Enum

class ScheduleStatusEnum(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    DELAYED = "delayed"

class ScheduleBase(BaseModel):
    departure_time: time = Field(..., description="Departure time")
    arrival_time: time = Field(..., description="Arrival time")
    price : Decimal = Field(..., gt=0, decimal_places=2, description="Ticket price")
    route_id : UUID = Field(..., description="Route ID")
    bus_id : UUID = Field(..., description="Bus ID")
    status: ScheduleStatusEnum = Field(ScheduleStatusEnum.ACTIVE, description="Status of the schedule (e.g., ACTIVE, CANCELLED, COMPLETED, DELAYED)")
    is_active: bool = Field(True, description="Indicates if the schedule is active")

    @field_validator("arrival_time")
    @classmethod
    def validate_times(cls, v, info):
        depature = info.data.get("departure_time")
        if depature and v <= depature:
            raise ValueError("Arrival time must be after departure time")
        return v


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    departure_time: Optional[time] = None
    arrival_time: Optional[time] = None
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    route_id: Optional[UUID] = None
    bus_id: Optional[UUID] = None
    status: Optional[ScheduleStatusEnum] = None
    is_active: Optional[bool] = None

    @field_validator("arrival_time")
    @classmethod
    def validate_times(cls, v, info):
        depature = info.data.get("departure_time")
        if depature and v <= depature:
            raise ValueError("Arrival time must be after departure time")
        return v


class ScheduleResponse(ScheduleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    route_origin: Optional[str] = None
    route_destination: Optional[str] = None
    bus_number: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        from_attributes = True









