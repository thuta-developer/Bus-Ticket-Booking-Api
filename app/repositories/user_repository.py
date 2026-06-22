from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func


from app.models.user import User
from app.core.database import get_db


class UserRepository:
    """
    Repository class for User model.
    Handles all database operations (CRUD) for users.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with an active database session.

        Args:
            db: AsyncSession instance from FastAPI dependency (get_db)
        """
        self.db = db

    # ========== READ Operations ==========

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get a user by their UUID primary key.

        Args:
            user_id: UUID of the user

        Returns:
            User object if found, else None
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address (case-insensitive search).
        
        Args:
            email: Email address to search for
            
        Returns:
            User object if found, else None
        """
        # PostgreSQL LOWER() သုံးပြီး case-insensitive ဖြစ်အောင်ရှာ
        stmt = select(User).where(User.email.ilike(email))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_user_by_email(self, email: str) -> Optional[User]:
        """
        Get an active user by email (used for login).
        Only returns users where is_active = True.
        
        Args:
            email: Email address
            
        Returns:
            Active User object if found, else None
        """
        
        stmt = select(User).where(and_(User.email.ilike(email), User.is_active == True))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    
    async def search_users(
    self,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    is_verified: Optional[bool] = None,
    account_type: Optional[str] = None,

    ) -> List[User]:
        """
        Search users by email or full_name with pagination.
        """
        stmt = select(User)
        
        # 1. Base filter: active/inactive
        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        # 2. Optional verified filter
        if is_verified is not None:
            stmt = stmt.where(User.is_verified == is_verified)

        if account_type is not None:
            stmt = stmt.where(User.account_type == account_type)
            
        # 3. Search Filter (case-insensitive)
        if search:
            stmt = stmt.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )

        # 4. Order by created_at (newest first)
        stmt = stmt.order_by(User.created_at.desc())
        
        # 5. Pagination
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count_search_user(
        self,
        search: Optional[str] = None,
        include_inactive: bool = False,
        is_verified: Optional[bool] = None,
        account_type: Optional[str] = None,
    ) -> int:
        """
        Count total users matching search (for pagination metadata).
        """
        stmt = select(func.count(User.id))
        
        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        if is_verified is not None:
            stmt = stmt.where(User.is_verified == is_verified)

        if account_type is not None:
            stmt = stmt.where(User.account_type == account_type)
            
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )

        result = await self.db.execute(stmt)
        return result.scalar()

        
        
    
    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[User]:
        """
        Get a list of users with pagination.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            include_inactive: If True, include inactive users
            
        Returns:
            List of User objects
        """
        stmt = select(User)
        
        if not include_inactive:
            stmt = stmt.where(User.is_active == True)
        
        stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count_users(self, include_inactive: bool = False) -> int:
        """
        Count total number of users.
        
        Args:
            include_inactive: If True, count all users including inactive
            
        Returns:
            Total count
        """
        from sqlalchemy import func
        
        stmt = select(func.count()).select_from(User)
        if not include_inactive:
            stmt = stmt.where(User.is_active == True)
            
        result = await self.db.execute(stmt)
        return result.scalar()

    # ========== CREATE Operations ==========
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Create a new user in the database.
        
        Args:
            user_data: Dictionary containing user fields
                      (email, full_name, hashed_password, etc.)
        
        Returns:
            Created User object
            
        Raises:
            IntegrityError: If email already exists (unique constraint violation)
        """
        try:
            new_user = User(**user_data)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            return new_user
        except IntegrityError as e:
            await self.db.rollback()
            # PostgreSQL unique violation error code = 23505
            if "23505" in str(e) or "duplicate key" in str(e).lower():
                raise ValueError("A user with this email already exists")
            raise e
        
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """
        Alias for create_user (kept for compatibility with service layer)
        """
        return await self.create_user(user_data)

    
    # ========== UPDATE Operations ==========
    
    async def update(
        self, 
        user_id: UUID, 
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """
        Update an existing user.
        
        Args:
            user_id: UUID of the user to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated User object if found, else None
        """
        # ဦးဆုံး user ရှိမရှိစစ်ပါ
        user = await self.get_by_id(user_id)
        if not user:
            return None

        # Update fields
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)  # PostgreSQL supports RETURNING
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        # RETURNING ရလာတဲ့ result ကို refresh မလိုဘဲ ပြန်ယူလို့ရတယ်
        updated_user = result.scalar_one_or_none()
        return updated_user
    
    async def update_last_login(self, user_id: UUID) -> None:
        """
        Update the last_login timestamp for a user.
        
        Args:
            user_id: UUID of the user
        """
        from sqlalchemy.sql import func
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login=func.now())
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
    async def verify_email(self, user_id: UUID) -> Optional[User]:
        """
        Mark a user's email as verified.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Updated User object if found, else None
        """
        from sqlalchemy.sql import func
        
        user = await self.get_by_id(user_id)
        if not user:
            return None

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True, verified_at=func.now())
            .returning(User)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()
    
    # ========== DELETE Operations ==========

    async def soft_delete(self, user_id: UUID) -> bool:
        """
        Soft delete a user (set is_active = False).
        This is preferred over hard delete for audit purposes.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if deleted, False if user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return True
    
    async def hard_delete(self, user_id: UUID) -> bool:
        """
        Permanently delete a user from the database.
        Use with caution! Usually we use soft_delete instead.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if deleted, False if user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True







        

        


        

        

        

    
