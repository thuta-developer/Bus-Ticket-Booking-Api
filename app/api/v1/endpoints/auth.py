from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenRefresh
from app.services.user_service import UserService
from app.api.deps import CurrentUser


# ============================================
# Router Definition
# ============================================
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        403: {"description": "Not enough permissions"}
    }
)

# ============================================
# 1. Register Endpoint
# ============================================
@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, full name, and password."
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: Must be a valid email address (unique)
    - **full_name**: User's full name (min 1, max 255 chars)
    - **password**: Min 8 chars, must contain at least 1 digit and 1 uppercase letter
    """
    service = UserService(db)
    result = await service.register_user(user_data)
    return result

    
    
# ============================================
# 2. Login Endpoint (Standard OAuth2)
# ============================================
@router.post(
    "/login",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description="Authenticate user and return JWT access & refresh tokens."
)
async def login(
    login_data: UserLogin,  # JSON body အနေနဲ့ လက်ခံမယ်
    db: AsyncSession = Depends(get_db)
):
    """
    Login using email and password (JSON body).
    """
    service = UserService(db)
    result = await service.login_user(login_data)
    return result




# ============================================
# 3. Refresh Token Endpoint
# ============================================
@router.post(
    "/refresh",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
async def refresh_token(
    body: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh an expired access token.

    Pass the refresh token in the JSON request body (not as a query parameter).
    """
    service = UserService(db)
    return await service.refresh_access_token(body.refresh_token)


# ============================================
# 4. Get Current User Profile (Me)
# ============================================
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user."
)
async def get_me(
    current_user: CurrentUser
):
    """
    Get the authenticated user's profile.
    
    Requires a valid access token in the Authorization header.
    """
    return current_user


# ============================================
# 5. Logout Endpoint (Client-side)
# ============================================
@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Client should discard the tokens. Server-side token blacklist not implemented yet."
)
async def logout(
    current_user: CurrentUser
):
    """
    Logout the current user.
    
    Since we're using stateless JWT, the server does not store tokens.
    The client must remove the tokens from storage.
    (Future: We'll add Redis-based token blacklist).
    """
    return {
        "message": f"User '{current_user.email}' successfully logged out",
        "detail": "Please discard your tokens on the client side."
    }