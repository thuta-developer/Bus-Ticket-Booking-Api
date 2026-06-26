from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    StaffUserCreate,
    UserCreate,
    UserUpdate,
    UserLogin,
    UserResponse,
)
from app.models.user import User
from app.models.role import Role
from app.models.user_role import user_roles
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class UserService:
    """
    Service layer for User business logic.
    Orchestrates Repository, Security, and Validation.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the service with a database session.
        Instantiates the UserRepository internally.
        """
        self.db = db
        self.repo = UserRepository(db)

    # ============================================
    # Authentication & Registration
    # ============================================
    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Register a new user.

        Steps:
        1. Check if email already exists
        2. Hash the password
        3. Create user in database
        4. Return user data (without password)
        """
        # 1. Check for existing user (case-insensitive)
        existing_user = await self.repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists",
            )

        # 2. Hash password
        hashed_password = get_password_hash(user_data.password)

        # 3. Prepare user data for creation
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        user_dict["account_type"] = "customer"

        # 4. Create user in database
        try:
            new_user = await self.repo.create(user_dict)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            ) from exc

        # 5. Generate tokens for auto-login after registration
        access_token = create_access_token(data={"sub": str(new_user.id)})
        refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

        # 6. Return user with tokens
        return {
            "user": UserResponse.model_validate(new_user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def create_staff_user(self, user_data: StaffUserCreate) -> UserResponse:
        """
        Create a dashboard staff user and optionally assign roles.
        """
        existing_user = await self.repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists",
            )

        user_dict = user_data.model_dump(exclude={"password", "role_ids"})
        user_dict["hashed_password"] = get_password_hash(user_data.password)

        new_user = await self.repo.create(user_dict)

        if user_data.role_ids:
            await self.assign_roles(new_user.id, user_data.role_ids)
            await self.db.refresh(new_user)

        return UserResponse.model_validate(new_user)

    async def login_user(self, login_data=UserLogin) -> Dict[str, Any]:
        """
        Authenticate a user and return tokens.

        Steps:
        1. Find active user by email
        2. Verify password
        3. Update last_login timestamp
        4. Generate tokens
        5. Return tokens and user data
        """
        # 1. Get active user by email
        user = await self.repo.get_active_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Update last_login and refresh user object
        await self.repo.update_last_login(user.id)
        await self.db.refresh(user)

        # 4. Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return {
            "user": UserResponse.model_validate(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh an expired access token using a valid refresh token.

        Steps:
        1. Decode refresh token
        2. Check token type is 'refresh'
        3. Check user exists and is active
        4. Generate new access token
        """

        # 1. Decode Token
        payload = decode_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Get user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
            )

        # 4. Check user exists and is active
        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # 5. Generate new access token
        new_access_token = create_access_token(data={"sub": str(user.id)})

        return {"access_token": new_access_token, "token_type": "bearer"}

    # ============================================
    # User Management (CRUD)
    # ============================================

    async def get_current_user(self, user_id: UUID) -> User:
        """
        Get the current authenticated user by ID.
        Raises 404 if not found or inactive.
        """
        user = await self.repo.get_by_id_with_roles_and_permissions(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or inactive",
            )
        return user

    async def get_user_profile(self, user_id: UUID) -> UserResponse:
        """
        Get a user's profile as a response schema.
        """
        user = await self.get_current_user(user_id)
        return UserResponse.model_validate(user)

    async def update_user_profile(
        self, user_id: UUID, update_data: UserUpdate
    ) -> UserResponse:
        """
        Update a user's profile.
        Handles password update securely.
        """
        # 1. Get existing user
        user = await self.get_current_user(user_id)

        # 2. Prepare update data
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update",
            )

        # 3. If password is being updated, hash it
        if "password" in update_dict:
            update_dict["hashed_password"] = get_password_hash(
                update_dict.pop("password")
            )

        # 4. Update user
        updated_user = await self.repo.update(user_id, update_dict)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return UserResponse.model_validate(updated_user)

    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """
        Get all roles assigned to a specific user.
        Returns list of Role objects with their details.
        """
        user = await self.repo.get_by_id_with_roles_and_permissions(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user.roles

    async def assign_roles(self, user_id: UUID, role_ids: List[UUID]) -> User:
        """
        Replace all roles for a user.
        """
        unique_role_ids = list(dict.fromkeys(role_ids))
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if unique_role_ids:
            stmt = select(Role.id).where(Role.id.in_(unique_role_ids))
            result = await self.db.execute(stmt)
            found_ids = result.scalars().all()
            if len(found_ids) != len(unique_role_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more role IDs are invalid",
                )

        await self.db.execute(
            delete(user_roles).where(user_roles.c.user_id == user_id)
        )

        if unique_role_ids:
            await self.db.execute(
                user_roles.insert(),
                [{"user_id": user_id, "role_id": role_id} for role_id in unique_role_ids],
            )

        await self.db.commit()
        user = await self.repo.get_by_id_with_roles_and_permissions(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def search_users(
        self,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        is_verified: Optional[bool] = None,
        account_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search users with pagination and filters.
        """
        users = await self.repo.search_users(
            search=search,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            is_verified=is_verified,
            account_type=account_type,
        )
        total = await self.repo.count_search_user(
            search=search,
            include_inactive=include_inactive,
            is_verified=is_verified,
            account_type=account_type,
        )
        
        return {
            "items": [UserResponse.model_validate(user) for user in users],
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total,
        }
        

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        """
        List users with pagination.
        """
        users = await self.repo.get_all_users(skip, limit, include_inactive)
        total = await self.repo.count_users(include_inactive)

        return {
            "items": [UserResponse.model_validate(user) for user in users],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def admin_update_user(
        self,
        user_id: UUID,
        update_dict: Dict[str, Any],
        role_ids: Optional[List[UUID]] = None,
    ) -> UserResponse:
        updated_user = None

        if update_dict:
            updated_user = await self.repo.update(user_id, update_dict)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found",
                )

        if role_ids is not None:
            updated_user = await self.assign_roles(user_id, role_ids)

        if updated_user is None:
            updated_user = await self.repo.get_by_id(user_id)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found",
                )

        return UserResponse.model_validate(updated_user)

    async def delete_user(
        self,
        user_id: UUID,
        *,
        actor: User,
        hard_delete: bool = False,
    ) -> None:
        """
        Delete a user (soft by default, hard if specified).
        Hard delete requires superuser privileges.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if actor.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot delete your own account",
            )

        if  not actor.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin can permanently delete users",
            )
            
        deleted = await self.repo.hard_delete(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )
