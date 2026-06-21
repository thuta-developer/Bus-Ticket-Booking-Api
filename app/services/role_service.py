from typing import Optional, List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import role_permissions
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse

class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_all(self, skip: int = 0 , limit: int = 100) -> List[Role]:
        stmt = select(Role).offset(skip).limit(limit).order_by(Role.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_id(self, role_id: UUID) -> Optional[Role]:
        stmt = select(Role).where(Role.id == role_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, role_data: RoleCreate) -> Role:
        # Check if role name exists
        existing = await self.get_by_name(role_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_data.name}' already exists"
            )

        # Create role
        role = Role(
            name=role_data.name,
            description=role_data.description,
            is_default=role_data.is_default
        )
        self.db.add(role)
        await self.db.flush()

        # Assign permissions if provided
        if role_data.permission_ids:
            await self._assign_permissions(role.id, role_data.permission_ids)

        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def update(self, role_id: UUID, role_data: RoleUpdate) -> Role:
        role = await self.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        # Update fields
        if role_data.name is not None:
            # Check if new name conflicts
            existing = await self.get_by_name(role_data.name)
            if existing and existing.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role '{role_data.name}' already exists"
                )
            role.name = role_data.name

        if role_data.description is not None:
            role.description = role_data.description

        if role_data.is_default is not None:
            role.is_default = role_data.is_default

        # Update permissions if provided
        if role_data.permission_ids is not None:
            await self._assign_permissions(role_id, role_data.permission_ids)

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete(self, role_id: UUID) -> bool:
        role = await self.get_by_id(role_id)
        if not role:
            return False

        # Check if this role is being used by any user
        if role.users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role '{role.name}' because it is assigned to users"
            )

        await self.db.delete(role)
        await self.db.commit()
        return True

    async def _assign_permissions(self, role_id: UUID, permission_ids: List[UUID]):
        """Assign permissions to a role (replace all existing)"""
        # Remove all existing permissions
        await self.db.execute(
            delete(role_permissions).where(role_permissions.c.role_id == role_id)
        )

        # Add new permissions
        if permission_ids:
            # Verify all permissions exist
            stmt = select(Permission.id).where(Permission.id.in_(permission_ids))
            result = await self.db.execute(stmt)
            found_ids = result.scalars().all()

            if len(found_ids) != len(permission_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more permission IDs are invalid"
                )

            # Insert new permissions
            for perm_id in permission_ids:
                stmt = role_permissions.insert().values(
                    role_id=role_id,
                    permission_id=perm_id
                )
                await self.db.execute(stmt)


