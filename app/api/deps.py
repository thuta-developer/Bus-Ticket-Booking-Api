from typing import Optional, Annotated,List
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository

# ============================================
# 1. OAuth2 Scheme (Token URL ကို သတ်မှတ်ခြင်း)
# ============================================
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True,  # Token မပါရင် အလိုအလျောက် 401 ပြန်ပေးမယ်
)

# ============================================
# 2. Credentials Exception (Standardized Error)
# ============================================
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# ============================================
# 3. Get Current User (Core Dependency)
# ============================================
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    JWT Token ကနေ လက်ရှိ User ကို ထုတ်ယူပေးတဲ့ Dependency

    Steps:
    1. Token ကို Decode လုပ်ပါ
    2. user_id (sub) ကို ထုတ်ယူပါ
    3. Database ကနေ User ကို ရှာပါ
    4. User ကို ပြန်ပေးပါ (မရှိရင် 401)

    ဒီ Dependency ကို API Endpoint မှာ ထည့်သုံးရင်
    သက်သေပြပြီးသား User object ကို ချက်ချင်းရပါမယ်။
    """
    # 1. Decode Token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # 2. Extract user_id (sub)
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    # 3. Validate UUID format
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # 4. Check token type (Access Token ဖြစ်မှသာ လက်ခံမယ်)
    token_type = payload.get("type")
    if token_type != "access":
        raise credentials_exception

    # 5. Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    # 6. Return user (Service layer ကို သုံးချင်ရင် ဒီမှာ သုံးလို့ရတယ်)
    # But we only need the user object here to keep it lightweight.
    return user


# ============================================
# 4. Get Current Active User (For most endpoints)
# ============================================
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    get_current_user ကိုသုံးပြီး User ရှိမရှိစစ်၊
    ပြီးရင် is_active=True ဖြစ်မှသာ ခွင့်ပြုမယ်။

    ဒါကို ပုံမှန် API Endpoint (၉၀%) မှာ သုံးပါမယ်။
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


# ============================================
# 5. Get Current Superuser (For Admin only)
# ============================================
async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Super Admin ဖြစ်မှသာ ခွင့်ပြုမယ်။
    Role & Permission system မရှိသေးတဲ့အတွက်
    is_superuser flag ကို သုံးထားတယ်။

    ဒါကို Admin/Super Admin endpoints တွေမှာသုံးမယ်။
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser required.",
        )
    return current_user


# ============================================
# 6. Optional Current User (For public APIs)
# ============================================
async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Token ပါရင်လည်း ရ၊ မပါရင်လည်း ရတဲ့ Optional Dependency
    (Public APIs အတွက် ဥပမာ - Bus Schedule ကြည့်တဲ့အခါ)
    """
    if token is None:
        return None

    try:
        user = await get_current_user(token, db)
        return user if user.is_active else None
    except HTTPException:
        return None


# ============================================
# 7. Type Aliases for Cleaner Code (Optional)
# ============================================
# ဒီလို Type Alias တွေသုံးရင် API Endpoints တွေမှာ
# `user: User = Depends(get_current_active_user)` အစား
# `current_user: CurrentUser = Depends(get_current_active_user)` ဆိုပြီး
# ပိုပြီး self-documenting ဖြစ်အောင်လုပ်လို့ရတယ်။

CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
OptionalCurrentUser = Annotated[Optional[User], Depends(get_optional_current_user)]


# ============================================
# 8. Permission Checker (RBAC)
# ============================================


async def has_permission(user: User, permission_name: str) -> bool:
    """
    Check if a user has a specific permission.
    Superusers bypass all permission checks.
    """
    # Superuser ဆိုရင် အကုန်ခွင့်ပြုမယ်
    if user.is_superuser:
        return True
    
    # User ရဲ့ Roles တွေကနေ Permissions ကိုရှာမယ်
    for role in user.roles:
        for perm in role.permissions:
            if perm.name == permission_name:
                return True
    return False

def require_permission(permission_name: str):
    """
    Dependency Factory - Returns a dependency that checks for a specific permission.
    
    Usage:
        @router.get("/users")
        async def list_users(
            current_user: User = Depends(require_permission("users:read"))
        ):
            ...
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not await has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: '{permission_name}'"
            )
        return current_user
    return permission_dependency

def require_any_permission(permission_names: List[str]):
    """
    Dependency Factory - Checks if user has ANY of the listed permissions.
    
    Usage:
        @router.get("/reports")
        async def get_report(
            current_user: User = Depends(require_any_permission(["reports:read", "audit:read"]))
        ):
            ...
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        for perm_name in permission_names:
            if await has_permission(current_user, perm_name):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions. Required one of: {', '.join(permission_names)}"
        )
    return permission_dependency
