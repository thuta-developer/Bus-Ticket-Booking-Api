from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class BusCompanyBase(BaseModel):
    name: str = Field(..., max_length=255, description="Company name (e.g., JJ Express)")
    description: Optional[str] = Field(None, description="Company description")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email address")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    address: Optional[str] = Field(None, max_length=255, description="Company address")
    logo_url: Optional[str] = Field(None, max_length=255, description="URL to the company's logo image")
    is_active: bool = Field(True, description="Indicates if the company is active")


class BusCompanyCreate(BusCompanyBase):
    pass

class BusCompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
 
class BusCompanyResponse(BusCompanyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True