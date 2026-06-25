from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator

# ============================================
# 1. Base Schema (Common fields)
# ============================================

class UserBase(BaseModel):
    """Shared properties for all User schemas."""
    email : EmailStr = Field(..., description="User's email address")
    full_name : str = Field(..., description="User's full name")
    
    class Config:
        from_attributes = True  # SQLAlchemy model ကနေ Pydantic ကို အလိုအလျောက်ပြောင်းဖို့ (ORM mode)


# ============================================
# 2. Create Schema (For Registration)
# ============================================
class UserCreate(UserBase):
    """Properties required for user registration."""
    password : str = Field(..., min_length=8, description="Password must be at least 8 characters")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password ခိုင်မာမှုကို အခြေခံကျကျ စစ်ဆေးခြင်း"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


# ============================================
# 3. Update Schema (For Profile Update)
# ============================================
class UserUpdate(BaseModel):
    """Properties that can be updated by the user."""
    
    full_name : Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

    
# ============================================
# 4. Login Schema (For Authentication)
# ============================================
class UserLogin(BaseModel):
    """Properties required for login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenRefresh(BaseModel):
    """Request body for refreshing an access token."""
    refresh_token: str = Field(..., min_length=1, description="Valid refresh token")

            
        
# ============================================
# 5. Response Schema (Return to Client)
# ============================================
class UserResponse(UserBase):
    """Properties returned to the client (Safe - No password hash)."""
    id: UUID
    is_active: bool
    is_verified: bool
    is_superuser: bool
    account_type: str
    last_login: Optional[datetime]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

        
# ============================================
# 6. Admin Update Schema (For Super Admin/Admin)
# ============================================
class UserAdminUpdate(BaseModel):
    """Properties that Admin can update."""
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    account_type: Optional[Literal["customer", "staff"]] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role_ids: Optional[List[UUID]] = None


class StaffUserCreate(UserBase):
    """Properties required for creating a dashboard staff account."""
    password: str = Field(..., min_length=8)
    account_type: Literal["staff"] = "staff"
    is_active: bool = True
    is_verified: bool = True
    is_superuser: bool = False
    role_ids: Optional[List[UUID]] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


class UserRoleAssign(BaseModel):
    """Assign or replace roles for a user."""
    role_ids: List[UUID]
