from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission, get_current_active_user
from app.schemas.promotion import (
    PromotionCreate,
    PromotionUpdate,
    PromotionResponse,
    PromotionUsageResponse,
    ApplyPromotionRequest,
    ApplyPromotionResponse,
)
from app.services.promotion_service import PromotionService
from app.models.promotion_usage import UsageStatus


router = APIRouter(
    prefix="/promotions",
    tags=["Promotions"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Not found"},
    },
)


# ============================================
# PUBLIC: Apply Promotion
# ============================================
@router.post(
    "/apply",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Apply a promotion code",
    description="Apply a promo code to get discount on booking.",
)
async def apply_promotion(
    request: ApplyPromotionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply a promotion code before creating a booking.
    This will validate the code and return the discount amount.
    """
    service = PromotionService(db)
    result = await service.apply_promotion(current_user.id, request)
    return {
        "status": "success",
        "data": result,
    }


# ============================================
# ADMIN: List Promotions
# ============================================
@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all promotions",
)
async def list_promotions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, code, or description"),
    status: Optional[str] = Query(None, description="Filter by status: active, expired, disabled"),
    include_inactive: bool = Query(False, description="Include inactive promotions"),
    current_user: User = Depends(require_permission("promotions:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PromotionService(db)
    result = await service.list_promotions(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        include_inactive=include_inactive,
    )
    return {"status": "success", "data": result}


# ============================================
# ADMIN: Get Promotion by ID
# ============================================
@router.get(
    "/{promotion_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get promotion by ID",
)
async def get_promotion(
    promotion_id: UUID,
    current_user: User = Depends(require_permission("promotions:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PromotionService(db)
    promotion = await service.get_promotion(promotion_id)
    return {"status": "success", "data": promotion}


# ============================================
# ADMIN: Create Promotion
# ============================================
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new promotion",
)
async def create_promotion(
    promo_data: PromotionCreate,
    current_user: User = Depends(require_permission("promotions:write")),
    db: AsyncSession = Depends(get_db),
):
    service = PromotionService(db)
    promotion = await service.create_promotion(promo_data)
    return {
        "status": "success",
        "message": "Promotion created successfully",
        "data": promotion,
    }


# ============================================
# ADMIN: Update Promotion
# ============================================
@router.put(
    "/{promotion_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update a promotion",
)
async def update_promotion(
    promotion_id: UUID,
    update_data: PromotionUpdate,
    current_user: User = Depends(require_permission("promotions:write")),
    db: AsyncSession = Depends(get_db),
):
    service = PromotionService(db)
    promotion = await service.update_promotion(promotion_id, update_data)
    return {
        "status": "success",
        "message": "Promotion updated successfully",
        "data": promotion,
    }


# ============================================
# ADMIN: Delete Promotion
# ============================================
@router.delete(
    "/{promotion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a promotion",
)
async def delete_promotion(
    promotion_id: UUID,
    current_user: User = Depends(require_permission("promotions:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = PromotionService(db)
    await service.delete_promotion(promotion_id)
    return None


# ============================================
# ADMIN: List Promotion Usages
# ============================================
@router.get(
    "/usages",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all promotion usages",
)
async def list_promotion_usages(
    promotion_id: Optional[UUID] = Query(None, description="Filter by promotion ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    status: Optional[UsageStatus] = Query(None, description="Filter by status: pending, success, cancelled"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("promotions:read")),
    db: AsyncSession = Depends(get_db),
):
    service = PromotionService(db)
    result = await service.list_promotion_usages(
        promotion_id=promotion_id,
        user_id=user_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return {"status": "success", "data": result}


# ============================================
# USER: Get My Promotions Usage
# ============================================
@router.get(
    "/my/usages",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get my promotion usages",
)
async def get_my_promotion_usages(
    status: Optional[UsageStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = PromotionService(db)
    usages = await service.get_user_promotion_usages(current_user.id, status)
    return {
        "status": "success",
        "data": usages,
    }


# ============================================
# ADMIN: Confirm Promotion Usage (After Booking)
# ============================================
@router.put(
    "/usages/{usage_id}/confirm",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Confirm promotion usage after booking",
)
async def confirm_promotion_usage(
    usage_id: UUID,
    booking_id: UUID = Query(..., description="Booking ID"),
    current_user: User = Depends(require_permission("promotions:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm promotion usage after successful payment.
    This updates the usage status from PENDING to SUCCESS.
    """
    service = PromotionService(db)
    usage = await service.confirm_promotion_usage(usage_id, booking_id)
    return {
        "status": "success",
        "message": "Promotion usage confirmed",
        "data": usage,
    }