from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_all(self, skip: int = 0 , limit: int = 100) -> List[Permission]:
        stmt = select(Permission).offset(skip).limit(limit).order_by(Permission.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_id(self, permission_id: UUID) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_by_name(self, name: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, perm_data: PermissionCreate) -> Permission:
        # Check if role name exists
        existing = await self.get_by_name(perm_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission '{perm_data.name}' already exists"
            )

        # Create role
        permission = Permission(**perm_data.model_dump())
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def update(self, permission_id: UUID, perm_data: PermissionUpdate) -> Permission:
        permission = await self.get_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )

        # Check name conflict
        if perm_data.name is not None:
            existing = await self.get_by_name(perm_data.name)
            if existing and existing.id != permission_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Permission '{perm_data.name}' already exists"
                )
            permission.name = perm_data.name

        if perm_data.resource is not None:
            permission.resource = perm_data.resource
        if perm_data.action is not None:
            permission.action = perm_data.action
        if perm_data.description is not None:
            permission.description = perm_data.description

        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def delete(self, permission_id: UUID) -> bool:
        permission = await self.get_by_id(permission_id)
        if not permission:
            return False

        # Production Safeguard: Core permissions ကိုမဖျက်ရ
        CORE_PERMISSIONS = ["users:read", "users:write", "roles:read", "roles:write", "permissions:read"]
        if permission.name in CORE_PERMISSIONS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot delete core permission: {permission.name}"
            )


        await self.db.delete(permission)
        await self.db.commit()
        return True
        