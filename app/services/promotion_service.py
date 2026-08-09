from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.promotion_repository import PromotionRepository
from app.repositories.user_repository import UserRepository
from app.models.promotion import PromotionStatus
from app.models.promotion_usage import UsageStatus
from app.schemas.promotion import (
    PromotionCreate,
    PromotionUpdate,
    PromotionResponse,
    PromotionUsageResponse,
    PromotionUsageCreate,
    ApplyPromotionRequest,
    ApplyPromotionResponse,
)


class PromotionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PromotionRepository(db)
        self.user_repo = UserRepository(db)

    # ============================================
    # VALIDATION HELPERS
    # ============================================

    def _validate_promotion(self, promotion) -> None:
        """Validate promotion is active, not expired, and not fully used."""
        if not promotion.is_active or promotion.status != PromotionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This promotion is not active"
            )

        if promotion.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This promotion has expired"
            )

        if promotion.is_fully_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This promotion has reached its usage limit"
            )

    async def _validate_user_usage(self, user_id: UUID, promotion_id: UUID) -> None:
        """Validate user hasn't exceeded max usage for this promotion."""
        usage_count = await self.repo.get_user_usage_count(
            user_id=user_id,
            promotion_id=promotion_id,
            status=UsageStatus.SUCCESS,
        )
        promotion = await self.repo.get_by_id(promotion_id)
        if promotion and usage_count >= promotion.max_usage_per_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already used this promotion {usage_count} time(s)"
            )

    def _calculate_discount(
        self,
        promotion,
        booking_total: float,
    ) -> Dict[str, Any]:
        """Calculate discount amount based on promotion rules."""
        discount_applied = 0.0

        # Percentage discount
        if promotion.discount_percentage:
            discount_applied = booking_total * (promotion.discount_percentage / 100)
            discount_type = "percentage"
        # Fixed amount discount
        elif promotion.discount_amount:
            discount_applied = promotion.discount_amount
            discount_type = "fixed"

        # Ensure discount doesn't exceed booking total
        if discount_applied > booking_total:
            discount_applied = booking_total
            discount_type = "full"

        return {
            "discount_applied": discount_applied,
            "discount_type": discount_type,
        }

    # ============================================
    # APPLY PROMOTION
    # ============================================

    async def apply_promotion(
        self,
        user_id: UUID,
        request: ApplyPromotionRequest,
    ) -> ApplyPromotionResponse:
        """
        Apply a promotion code to a booking.
        """
        # 1. Get promotion by code
        promotion = await self.repo.get_by_code(request.promo_code)
        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid promo code"
            )

        # 2. Validate promotion
        self._validate_promotion(promotion)

        # 3. Validate user usage
        await self._validate_user_usage(user_id, promotion.id)

        # 4. Calculate discount
        discount_info = self._calculate_discount(promotion, request.booking_total)

        # 5. Create pending usage
        usage_data = PromotionUsageCreate(
            promotion_id=promotion.id,
            user_id=user_id,
            discount_amount_applied=discount_info["discount_applied"],
            booking_id=None,  # Will be updated when booking is created
        )
        usage = await self.repo.create_usage(
            usage_data.model_dump(exclude_unset=True, exclude_none=True)
        )

        return ApplyPromotionResponse(
            promotion_id=promotion.id,
            promo_code=promotion.promo_code,
            promotion_name=promotion.name,
            discount_percentage=promotion.discount_percentage,
            discount_amount=promotion.discount_amount,
            discount_applied=discount_info["discount_applied"],
            final_total=request.booking_total - discount_info["discount_applied"],
            is_valid=True,
            message=f"Promo code applied successfully! You saved {discount_info['discount_applied']:.2f} MMK",
        )

    # ============================================
    # CONFIRM PROMOTION (After Booking/Payment)
    # ============================================

    async def confirm_promotion_usage(
        self,
        usage_id: UUID,
        booking_id: UUID,
    ) -> PromotionUsageResponse:
        """
        Confirm promotion usage after successful booking/payment.
        """
        usage = await self.repo.get_usage_by_id(usage_id)
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion usage not found"
            )

        if usage.status == UsageStatus.SUCCESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Promotion already confirmed"
            )

        # Update usage status to SUCCESS
        updated = await self.repo.update_usage(
            usage_id,
            {
                "status": UsageStatus.SUCCESS,
                "booking_id": booking_id,
            }
        )

        return PromotionUsageResponse.model_validate(updated)

    # ============================================
    # PROMOTION CRUD
    # ============================================

    async def create_promotion(self, promo_data: PromotionCreate) -> PromotionResponse:
        try:
            promotion = await self.repo.create(promo_data.model_dump())
            return PromotionResponse.model_validate(promotion)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def get_promotion(self, promotion_id: UUID) -> PromotionResponse:
        promotion = await self.repo.get_by_id(promotion_id)
        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )
        return PromotionResponse.model_validate(promotion)

    async def get_promotion_by_code(self, promo_code: str) -> PromotionResponse:
        promotion = await self.repo.get_by_code(promo_code)
        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )
        return PromotionResponse.model_validate(promotion)

    async def list_promotions(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        promotions = await self.repo.get_all(
            skip=skip,
            limit=limit,
            search=search,
            status=status,
            include_inactive=include_inactive,
        )
        total = await self.repo.count(
            search=search,
            status=status,
            include_inactive=include_inactive,
        )

        items = [PromotionResponse.model_validate(p) for p in promotions]

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "search": search,
        }

    async def update_promotion(
        self,
        promotion_id: UUID,
        update_data: PromotionUpdate,
    ) -> PromotionResponse:
        # Check if promotion exists
        existing = await self.repo.get_by_id(promotion_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )

        try:
            promotion = await self.repo.update(promotion_id, update_dict)
            return PromotionResponse.model_validate(promotion)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def delete_promotion(self, promotion_id: UUID) -> None:
        promotion = await self.repo.get_by_id(promotion_id)
        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )
        await self.repo.delete(promotion_id)

    # ============================================
    # PROMOTION USAGE
    # ============================================

    async def list_promotion_usages(
        self,
        promotion_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        status: Optional[UsageStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        usages = await self.repo.get_all_usages(
            promotion_id=promotion_id,
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit,
        )

        items = []
        for usage in usages:
            response = PromotionUsageResponse.model_validate(usage)
            if usage.user:
                response.user_email = usage.user.email
            items.append(response)

        return {
            "items": items,
            "skip": skip,
            "limit": limit,
            "total": len(items),
        }

    async def get_user_promotion_usages(
        self,
        user_id: UUID,
        status: Optional[UsageStatus] = None,
    ) -> List[PromotionUsageResponse]:
        usages = await self.repo.get_all_usages(
            user_id=user_id,
            status=status,
        )
        return [PromotionUsageResponse.model_validate(u) for u in usages]