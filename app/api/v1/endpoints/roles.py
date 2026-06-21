from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.services.role_service import RoleService

router = APIRouter(
    prefix="/roles",
    tags=["Roles & Permissions - Admin"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
    },
)


@router.get(
    "/",
    response_model=List[RoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all roles",
)
async def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_permission("roles:read")),
    db: AsyncSession = Depends(get_db),
):
    service = RoleService(db)
    result = await service.get_all(skip, limit)
    return result


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get role by ID",
)
async def get_role(
    role_id: UUID,
    current_user: User = Depends(require_permission("roles:read")),
    db: AsyncSession = Depends(get_db),
):
    service = RoleService(db)
    role = await service.get_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role

@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_permission("roles:write")),
    db: AsyncSession = Depends(get_db),
):
    service = RoleService(db)
    role = await service.create(role_data)
    return role


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a role",
)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(require_permission("roles:write")),
    db: AsyncSession = Depends(get_db),
):
    service = RoleService(db)
    role = await service.update(role_id, role_data)
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
)
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(require_permission("roles:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = RoleService(db)
    deleted = await service.delete(role_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return None
