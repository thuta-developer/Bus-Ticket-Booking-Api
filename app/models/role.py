from sqlalchemy import Column, String, Boolean, Text
from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from app.models.user_role import user_roles
from app.models.role_permission import role_permissions



class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Role name: super_admin, admin, bus_operator, customer"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of the role"
    )
    
    is_default = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is this the default role for new users? (e.g., customer)"
    )
    
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin",
    )

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Role {self.name}>"