from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.feature import Feature


class FeatureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Read Operations
    # ============================================
    async def get_by_id(self, feature_id: UUID) -> Optional[Feature]:
        stmt = select(Feature).where(Feature.id == feature_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Feature]:
        stmt = select(Feature).where(Feature.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, feature_ids: List[UUID]) -> List[Feature]:
        if not feature_ids:
            return []
        stmt = select(Feature).where(Feature.id.in_(feature_ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[Feature]:
        stmt = select(Feature)

        # Filters
        if not include_inactive:
            stmt = stmt.where(Feature.is_active == True)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Feature.name.ilike(search_term),
                    Feature.description.ilike(search_term),
                )
            )

        stmt = stmt.offset(skip).limit(limit).order_by(Feature.name.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(
        self, search: Optional[str] = None, include_inactive: bool = False
    ) -> int:
        stmt = select(func.count()).select_from(Feature)

        # Filters
        if not include_inactive:
            stmt = stmt.where(Feature.is_active == True)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Feature.name.ilike(search_term),
                    Feature.description.ilike(search_term),
                )
            )

        result = await self.db.execute(stmt)
        return result.scalar_one()

    # ============================================
    # Create Operation
    # ============================================
    async def create(self, feature_data: dict) -> Feature:
        try:
            feature = Feature(**feature_data)
            self.db.add(feature)
            await self.db.commit()
            await self.db.refresh(feature)
            return feature
        except IntegrityError as e:
            await self.db.rollback()
            if "name" in str(e).lower():
                raise ValueError("Feature name already exists.")
            raise e

    # ============================================
    # Update Operation
    # ============================================
    async def update(self, feature_id: UUID, update_data: dict) -> Optional[Feature]:
        feature = await self.get_by_id(feature_id)
        if not feature:
            return None

        try:
            stmt = (
                update(Feature)
                .where(Feature.id == feature_id)
                .values(**update_data)
                .returning(Feature)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            await self.db.rollback()
            if "name" in str(e).lower():
                raise ValueError("Feature name already exists.")
            raise e

    # ============================================
    # Delete Operations
    # ============================================
    async def delete(self, feature_id: UUID) -> bool:
        feature = await self.get_by_id(feature_id)
        if not feature:
            return False

        await self.db.delete(feature)
        await self.db.commit()
        return True

    async def soft_delete(self, feature_id: UUID) -> bool:
        feature = await self.get_by_id(feature_id)
        if not feature:
            return False

        feature.is_active = False
        await self.db.commit()
        return True