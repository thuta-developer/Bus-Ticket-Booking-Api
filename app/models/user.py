from sqlalchemy import Column, Integer, String, DateTime, Index, Boolean
from sqlalchemy.sql import func
from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from app.models.user_role import user_roles


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True,comment="User's unique email address (used for login)")
    full_name = Column(String(255), nullable=False, comment="User's full name")
    hashed_password = Column(String(255), nullable=False, comment="Bcrypt hashed password (never store plain text)")
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Can this user log in? (Soft delete / Suspension)"
    )
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Has the user verified their email?"
    )
    
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bypass all permissions? (Super Admin)"
    )

    account_type = Column(
        String(20),
        default="customer",
        nullable=False,
        comment="Account type: customer or staff"
    )

    # ========== Timestamps (Extra) ==========
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )
    
    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the email was verified"
    )
    
    # ========== Relationships ==========
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )
    
    # ========== Indexes for Performance ==========
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),  # Login query မြန်ဆန်စေရန်
        Index("ix_users_account_type", "account_type"),
    )

    def __repr__(self):
        return f"<User {self.email}>"
