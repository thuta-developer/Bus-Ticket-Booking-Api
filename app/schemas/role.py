from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base schema for Role"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_default: bool = False


class RoleCreate(RoleBase):
    """Schema for creating a new role"""
    permission_ids: Optional[List[UUID]] = Field(
        None, 
        description="List of permission UUIDs to assign to this role"
    )


class RoleUpdate(BaseModel):
    """Schema for updating a role"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None
    permission_ids: Optional[List[UUID]] = Field(
        None,
        description="List of permission UUIDs to assign to this role"
    )


class RoleResponse(RoleBase):
    """Schema for role response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    permissions: Optional[List["PermissionResponse"]] = []

    class Config:
        from_attributes = True


# Import here to avoid circular import
from app.schemas.permission import PermissionResponse
RoleResponse.model_rebuild()