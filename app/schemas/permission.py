from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """Base schema for Permission"""
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=255)


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    """Schema for updating a permission"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    resource: Optional[str] = Field(None, min_length=1, max_length=50)
    action: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=255)


class PermissionResponse(PermissionBase):
    """Schema for permission response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True