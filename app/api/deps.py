from typing import Optional, Annotated, List
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import user_has_any_permission, user_has_permission
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True,
)

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _resolve_user_from_token(
    token: str,
    db: AsyncSession,
    *,
    load_rbac: bool = False,
) -> User:
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_repo = UserRepository(db)
    if load_rbac:
        user = await user_repo.get_by_id_with_roles_and_permissions(user_id)
    else:
        user = await user_repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Lightweight auth — user row only (no roles/permissions)."""
    return await _resolve_user_from_token(token, db, load_rbac=False)


async def get_current_user_for_rbac(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Auth with roles and permissions eager-loaded for RBAC checks."""
    return await _resolve_user_from_token(token, db, load_rbac=True)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_active_user_for_rbac(
    current_user: User = Depends(get_current_user_for_rbac),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user_for_rbac),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser required.",
        )
    return current_user


async def get_current_staff_user(
    current_user: User = Depends(get_current_active_user_for_rbac),
) -> User:
    if current_user.is_superuser:
        return current_user

    if current_user.account_type != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dashboard access requires a staff account.",
        )
    return current_user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None

    try:
        user = await _resolve_user_from_token(token, db, load_rbac=False)
        return user if user.is_active else None
    except HTTPException:
        return None


CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
CurrentStaffUser = Annotated[User, Depends(get_current_staff_user)]
OptionalCurrentUser = Annotated[Optional[User], Depends(get_optional_current_user)]


def require_permission(permission_name: str):
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user_for_rbac),
    ) -> User:
        if not user_has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: '{permission_name}'",
            )
        return current_user

    return permission_dependency


def require_staff_permission(permission_name: str):
    async def permission_dependency(
        current_user: User = Depends(get_current_staff_user),
    ) -> User:
        if not user_has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: '{permission_name}'",
            )
        return current_user

    return permission_dependency


def require_any_permission(permission_names: List[str]):
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user_for_rbac),
    ) -> User:
        if not user_has_any_permission(current_user, permission_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required one of: {', '.join(permission_names)}",
            )
        return current_user

    return permission_dependency
