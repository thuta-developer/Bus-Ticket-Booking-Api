from sqlalchemy import Column, String, Text
from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from app.models.role_permission import role_permissions


class Permission(BaseModel):
    __tablename__ = "permissions"

    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Permission name: users:read, bookings:write, etc."
    )
    
    resource = Column(
        String(50),
        nullable=False,
        comment="Resource name: users, bookings, buses, routes, etc."
    )
    
    action = Column(
        String(20),
        nullable=False,
        comment="Action: create, read, update, delete, manage"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description"
    )
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )


    def __repr__(self):
        return f"<Permission {self.name}>"