from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.promotion import Promotion, PromotionStatus
from app.models.promotion_usage import PromotionUsage, UsageStatus


class PromotionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, promotion_id: UUID) -> Optional[Promotion]:
        stmt = select(Promotion).where(Promotion.id == promotion_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, promo_code: str) -> Optional[Promotion]:
        stmt = select(Promotion).where(Promotion.promo_code == promo_code.upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[Promotion]:
        stmt = select(Promotion)

        if not include_inactive:
            stmt = stmt.where(Promotion.is_active == True)

        if status:
            stmt = stmt.where(Promotion.status == status)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Promotion.name.ilike(search_term),
                    Promotion.promo_code.ilike(search_term),
                    Promotion.description.ilike(search_term),
                )
            )

        stmt = stmt.offset(skip).limit(limit).order_by(desc(Promotion.created_at))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> int:
        stmt = select(func.count()).select_from(Promotion)

        if not include_inactive:
            stmt = stmt.where(Promotion.is_active == True)

        if status:
            stmt = stmt.where(Promotion.status == status)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Promotion.name.ilike(search_term),
                    Promotion.promo_code.ilike(search_term),
                    Promotion.description.ilike(search_term),
                )
            )

        result = await self.db.execute(stmt)
        return result.scalar()

    async def create(self, promotion_data: dict) -> Promotion:
        try:
            promotion = Promotion(**promotion_data)
            self.db.add(promotion)
            await self.db.commit()
            await self.db.refresh(promotion)
            return promotion
        except IntegrityError as e:
            await self.db.rollback()
            if "promo_code" in str(e).lower():
                raise ValueError("Promo code already exists")
            raise e

    async def update(self, promotion_id: UUID, update_data: dict) -> Optional[Promotion]:
        try:
            stmt = (
                update(Promotion)
                .where(Promotion.id == promotion_id)
                .values(**update_data)
                .returning(Promotion)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            await self.db.rollback()
            if "promo_code" in str(e).lower():
                raise ValueError("Promo code already exists")
            raise e

    async def delete(self, promotion_id: UUID) -> bool:
        promotion = await self.get_by_id(promotion_id)
        if not promotion:
            return False
        await self.db.delete(promotion)
        await self.db.commit()
        return True

    # ============================================
    # PROMOTION USAGE
    # ============================================

    async def get_usage_by_id(self, usage_id: UUID) -> Optional[PromotionUsage]:
        stmt = select(PromotionUsage).where(PromotionUsage.id == usage_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_usage_by_user_and_promo(
        self,
        user_id: UUID,
        promotion_id: UUID,
        status: Optional[UsageStatus] = None,
    ) -> Optional[PromotionUsage]:
        stmt = select(PromotionUsage).where(
            and_(
                PromotionUsage.user_id == user_id,
                PromotionUsage.promotion_id == promotion_id,
            )
        )
        if status:
            stmt = stmt.where(PromotionUsage.status == status)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_usage_count(
        self,
        user_id: UUID,
        promotion_id: UUID,
        status: Optional[UsageStatus] = None,
    ) -> int:
        stmt = select(func.count()).select_from(PromotionUsage).where(
            and_(
                PromotionUsage.user_id == user_id,
                PromotionUsage.promotion_id == promotion_id,
            )
        )
        if status:
            stmt = stmt.where(PromotionUsage.status == status)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_all_usages(
        self,
        promotion_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        status: Optional[UsageStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[PromotionUsage]:
        stmt = select(PromotionUsage)

        if promotion_id:
            stmt = stmt.where(PromotionUsage.promotion_id == promotion_id)

        if user_id:
            stmt = stmt.where(PromotionUsage.user_id == user_id)

        if status:
            stmt = stmt.where(PromotionUsage.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(desc(PromotionUsage.created_at))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_usage(self, usage_data: dict) -> PromotionUsage:
        usage = PromotionUsage(**usage_data)
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def update_usage(self, usage_id: UUID, update_data: dict) -> Optional[PromotionUsage]:
        stmt = (
            update(PromotionUsage)
            .where(PromotionUsage.id == usage_id)
            .values(**update_data)
            .returning(PromotionUsage)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def update_usage_status(
        self,
        usage_id: UUID,
        status: UsageStatus,
    ) -> Optional[PromotionUsage]:
        return await self.update_usage(usage_id, {"status": status})

