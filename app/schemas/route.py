from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class RouteBase(BaseModel):
    name: str = Field(...,min_length=1, max_length=255, description="Route name")
    origin : str = Field(..., min_length=1, max_length=255, description="Origin city")
    destination : str = Field(..., min_length=1, max_length=255, description="Destination city")
    distance : Optional[float] = Field(None, ge=0, description="Distance in kilometers")
    duration_minutes : Optional[int] = Field(None, ge=1)
    base_price : float = Field(..., ge=0)
    description : Optional[str] = Field(None)
    is_active: bool = Field(True, description="Is this route active?")


class RouteCreate(RouteBase):
    @field_validator("origin")
    @classmethod
    def validate_origin (cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Origin cannot be empty")
        return v.strip()

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Destination cannot be empty")
        return v.strip()

    @field_validator("origin", "destination")
    @classmethod
    def validate_origin_destination(cls, v:str, info) -> str:
        if info.field_name == "origin" and v == info.data.get("destination"):
            raise ValueError("Origin and destination cannot be the same")
        return v


class RouteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    origin: Optional[str] = Field(None, min_length=1, max_length=100)
    destination: Optional[str] = Field(None, min_length=1, max_length=100)
    distance: Optional[float] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=1)
    base_price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None



class RouteResponse(RouteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True