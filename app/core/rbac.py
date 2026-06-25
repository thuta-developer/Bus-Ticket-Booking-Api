"""RBAC helpers — permission resolution without redundant DB round-trips."""

from typing import FrozenSet

from app.models.user import User

PERMISSIONS_ATTR = "_permission_names"


def resolve_user_permissions(user: User) -> FrozenSet[str]:
    """
    Build a set of permission names from eagerly-loaded roles.
    Caller must load User.roles and Role.permissions via selectinload first.
    """
    cached = getattr(user, PERMISSIONS_ATTR, None)
    if cached is not None:
        return cached

    names: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            names.add(perm.name)

    frozen = frozenset(names)
    object.__setattr__(user, PERMISSIONS_ATTR, frozen)
    return frozen


def user_has_permission(user: User, permission_name: str) -> bool:
    if user.is_superuser:
        return True
    return permission_name in resolve_user_permissions(user)


def user_has_any_permission(user: User, permission_names: list[str]) -> bool:
    if user.is_superuser:
        return True
    user_perms = resolve_user_permissions(user)
    return any(name in user_perms for name in permission_names)
