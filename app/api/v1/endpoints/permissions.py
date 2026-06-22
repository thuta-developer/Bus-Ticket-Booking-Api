from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_staff_permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionResponse
from app.services.permission_service import PermissionService

router = APIRouter(
    prefix="/permissions",
    tags=["Roles & Permissions - Admin"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
    },
)

@router.get(
    "/",
    response_model=List[PermissionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all permissions",
)
async def get_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_staff_permission("permissions:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PermissionService(db)
    return await service.get_all(skip, limit)

@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get permission by ID",
)
async def get_permission(
    permission_id: UUID,
    current_user: User = Depends(require_staff_permission("permissions:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PermissionService(db)
    permission = await service.get_by_id(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission

@router.post(
    "/",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new permission",
)
async def create_permission(
    perm_data: PermissionCreate,
    current_user: User = Depends(require_staff_permission("permissions:write")),
    db: AsyncSession = Depends(get_db),
):
    service = PermissionService(db)
    return await service.create(perm_data)

@router.put(
    "/{permission_id}",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a permission",
)
async def update_permission(
    permission_id: UUID,
    perm_data: PermissionUpdate,
    current_user: User = Depends(require_staff_permission("permissions:write")),
    db: AsyncSession = Depends(get_db),
):
    service = PermissionService(db)
    return await service.update(permission_id, perm_data)

@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a permission",
)
async def delete_permission(
    permission_id: UUID,
    current_user: User = Depends(require_staff_permission("permissions:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = PermissionService(db)
    deleted = await service.delete(permission_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return None
