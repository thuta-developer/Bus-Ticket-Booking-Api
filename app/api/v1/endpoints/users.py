from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserAdminUpdate
from app.services.user_service import UserService
from app.api.deps import (
    CurrentUser,  # Active User ကိုယ်တိုင်
    require_permission,  # Permission Checker
)

# ============================================
# Router Definition
# ============================================
router = APIRouter(
    prefix="/users",
    tags=["User Management (Admin)"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions (RBAC)"},
        404: {"description": "User not found"},
    },
)


# ============================================
# 1. List All Users (Admin Only)
# Permission Required: users:read
# ============================================
@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin)",
    description="Get a paginated list of users. Requires 'users:read' permission.",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    current_user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated user list. Only users with 'users:read' permission can access.
    """
    service = UserService(db)
    result = await service.list_users(skip, limit, include_inactive)
    return {"status": "success", "data": result}


# ============================================
# 2. Get User by ID (Admin Only)
# Permission Required: users:read
# ============================================
@router.get(
    "/{user_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID (Admin)",
    description="Get detailed information of a specific user. Requires 'users:read' permission.",
)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific user by UUID. Admin only.
    """
    service = UserService(db)
    user = await service.get_current_user(user_id)
    return {"status": "success", "data": UserResponse.model_validate(user)}


# ============================================
# 3. Update User (Admin Only)
# Permission Required: users:write
# ============================================
@router.put(
    "/{user_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update user by admin",
    description="Update any user's details (activate, verify, change role). Requires 'users:write' permission.",
)
async def update_user(
    user_id: UUID,
    update_data: UserAdminUpdate,
    current_user: User = Depends(require_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-only user update. Can modify is_active, is_verified, is_superuser, etc.
    """
    service = UserService(db)

    # Filter out unset fields
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update",
        )

    # Update user
    updated_user = await service.repo.update(user_id, update_dict)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return {
        "status": "success",
        "message": "User updated successfully",
        "data": UserResponse.model_validate(updated_user),
    }


# ============================================
# 4. Delete User (Admin Only)
# Permission Required: users:delete
# ============================================
@router.delete(
    "/{user_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete user (Admin)",
    description="Soft delete (default) or hard delete a user. Requires 'users:delete' permission.",
)
async def delete_user(
    user_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete from database"),
    current_user: User = Depends(require_permission("users:delete")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user. 'hard_delete=True' will permanently remove the record (use with caution).
    """
    service = UserService(db)
    await service.delete_user(user_id, hard_delete)
    return {
        "status": "success",
        "message": f"User {'hard ' if hard_delete else 'soft '}deleted successfully",
    }


# ============================================
# 5. Get Own Profile (User self-service)
# No special permission needed, just authentication.
# ============================================
@router.get(
    "/me/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get own profile",
    description="Get the profile of the currently authenticated user. (No special permission required)",
)
async def get_my_profile(
    current_user: CurrentUser,  # Just logged-in user
):
    """
    Returns the profile of the authenticated user.
    Equivalent to /auth/me, but placed here for RESTful consistency.
    """
    return current_user
