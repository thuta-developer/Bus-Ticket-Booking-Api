from typing import Optional,List
from uuid import UUID
from datetime import datetime, time,date
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
from enum import Enum

from app.schemas.bus import BusResponse
from app.schemas.seat import SeatResponse
from app.schemas.feature import FeatureResponse
from app.schemas.bus_image import BusImageResponse
from app.schemas.seat_layout import SeatLayoutResponse

class ScheduleStatusEnum(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    DELAYED = "delayed"

class ScheduleBase(BaseModel):
    departure_time: time = Field(..., description="Departure time")
    arrival_time: time = Field(..., description="Arrival time")
    route_id : UUID = Field(..., description="Route ID")
    bus_id : UUID = Field(..., description="Bus ID")
    status: ScheduleStatusEnum = Field(ScheduleStatusEnum.ACTIVE, description="Status of the schedule (e.g., ACTIVE, CANCELLED, COMPLETED, DELAYED)")
    is_active: bool = Field(True, description="Indicates if the schedule is active")

    # Dynamic Pricing
    local_price: Decimal = Field(..., ge=0, decimal_places=2, description="Price for locals")
    foreigner_price: Decimal = Field(..., ge=0, decimal_places=2, description="Price for foreigners")
    local_festival_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    foreigner_festival_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    # Booking Window
    booking_open_date: datetime = Field(..., description="When booking starts")
    booking_close_date: datetime = Field(..., description="When booking ends")
    
    # Festival Date Range
    festival_start_date: Optional[datetime] = Field(None, description="Festival period start")
    festival_end_date: Optional[datetime] = Field(None, description="Festival period end")


    @model_validator(mode="after")
    def validate_dates(self):
        # # Arrival must be after departure
        # if self.arrival_time <= self.departure_time:
        #     raise ValueError("Arrival time must be after departure time")
        
        # Booking open must be before booking close
        if self.booking_open_date >= self.booking_close_date:
            raise ValueError("Booking open date must be before booking close date")

        # Festival date range validation
        if self.festival_start_date and self.festival_end_date:
            if self.festival_start_date >= self.festival_end_date:
                raise ValueError("Festival start date must be before festival end date")

        # Only validate festival prices if they are actually set (not None and not 0)
        has_festival_price = (
            (self.local_festival_price is not None and self.local_festival_price > 0)
            or (self.foreigner_festival_price is not None and self.foreigner_festival_price > 0)
        )
        if has_festival_price:
            if not self.festival_start_date or not self.festival_end_date:
                raise ValueError("Festival date range must be set when festival prices are provided")

        return self


        




class ScheduleCreate(ScheduleBase):
    pass



class ScheduleUpdate(BaseModel):
    departure_time: Optional[time] = None
    arrival_time: Optional[time] = None
    route_id: Optional[UUID] = None
    bus_id: Optional[UUID] = None
    status: Optional[ScheduleStatusEnum] = None
    is_active: Optional[bool] = None
    local_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    foreigner_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    local_festival_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    foreigner_festival_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    booking_open_date: Optional[datetime] = None
    booking_close_date: Optional[datetime] = None
    festival_start_date: Optional[datetime] = None
    festival_end_date: Optional[datetime] = None




class ScheduleResponse(ScheduleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    route_origin: Optional[str] = None
    route_destination: Optional[str] = None
    bus_number: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    bus_type : Optional[str] = None

    class Config:
        from_attributes = True



# ====== Price Calculator Helper ======
class SchedulePriceResponse(BaseModel):
    schedule_id: UUID
    base_price: Decimal
    final_price: Decimal
    price_type: str  # local / foreigner / festival local / festival foreigner
    is_festival: bool
    user_type: str  # local / foreigner
    currency: str = "MMK"



# ===== Search Filter Schema ======
class ScheduleSearchFilter(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_date: Optional[date] = Field(None, description="Date of travel (YYYY-MM-DD)")
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bus_type: Optional[str] = None
    user_type: str = "local"  # "local" or "foreigner"
    include_festival: bool = False
    include_bookable_only: bool = True
    time_of_day: Optional[str] = Field(
        None,
        description="morning, afternoon, or night"
    )

class ScheduleDetailResponse(ScheduleResponse):
    """Schedule detail with bus, seats, features, images"""
    
    # Bus detail (full bus info)
    bus: Optional[BusResponse] = None
    
    # Seat layout
    seats: List[SeatResponse] = Field(default_factory=list)
    
    # Seat layout configuration
    seat_layout: Optional[SeatLayoutResponse] = None
    
    # Price calculation for the user
    price: Optional[SchedulePriceResponse] = None
