from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    StaffUserCreate,
    UserResponse,
    UserAdminUpdate,
    UserRoleAssign,
)
from app.services.user_service import UserService
from app.api.deps import (
    CurrentUser,  # Active User ကိုယ်တိုင်
    require_staff_permission,  # Staff Permission Checker
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
    summary="List or search users (Admin)",
)
async def list_users(
    search: Optional[str] = Query(
        None,
        min_length=1,
        max_length=100,
        description="Search by email or full name (case-insensitive)"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    is_verified: Optional[bool] = Query(
        None,
        description="Filter by email verification status"
    ),
    account_type: Optional[Literal["customer", "staff"]] = Query(
        None,
        description="Filter by account type"
    ),
    current_user: User = Depends(require_staff_permission("users:read")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated user list with search functionality.
    """
    service = UserService(db)
    result = await service.search_users(
        search=search,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
        is_verified=is_verified,
        account_type=account_type,
    )
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
    current_user: User = Depends(require_staff_permission("users:read")),
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
    current_user: User = Depends(require_staff_permission("users:write")),
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

    role_ids = update_dict.pop("role_ids", None)

    if "is_superuser" in update_dict and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can change superuser status",
        )

    updated_user = await service.admin_update_user(
        user_id,
        update_dict,
        role_ids=role_ids,
    )

    return {
        "status": "success",
        "message": "User updated successfully",
        "data": updated_user,
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
    current_user: User = Depends(require_staff_permission("users:delete")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user. 'hard_delete=True' will permanently remove the record (use with caution).
    """
    service = UserService(db)
    await service.delete_user(user_id, actor=current_user, hard_delete=hard_delete)
    return {
        "status": "success",
        "message": f"User {'hard ' if hard_delete else 'soft '}deleted successfully",
    }


@router.post(
    "/staff/accounts",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create staff user (Admin)",
)
async def create_staff_user(
    user_data: StaffUserCreate,
    current_user: User = Depends(require_staff_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a dashboard staff account and optionally assign roles.
    """
    if user_data.is_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can create another super admin",
        )

    service = UserService(db)
    user = await service.create_staff_user(user_data)
    return {
        "status": "success",
        "message": "Staff user created successfully",
        "data": user,
    }


@router.put(
    "/{user_id}/roles",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Assign roles to user (Admin)",
)
async def assign_user_roles(
    user_id: UUID,
    role_data: UserRoleAssign,
    current_user: User = Depends(require_staff_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Replace all roles for a user.
    """
    service = UserService(db)
    user = await service.assign_roles(user_id, role_data.role_ids)
    return {
        "status": "success",
        "message": "User roles updated successfully",
        "data": UserResponse.model_validate(user),
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
