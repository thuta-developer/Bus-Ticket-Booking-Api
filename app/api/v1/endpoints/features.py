from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.feature import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
)
from app.services.feature_service import FeatureService

router = APIRouter(
    prefix="/features",
    tags=["Features"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Feature not found"},
    },
)

@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all features",
    description="Public endpoint to list features (active only by default)",
)
async def list_features(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit : int = Query(20, ge=1, le=100, description="Maximum records to return"),
    search : Optional[str] = Query(
        None, description="Search by feature name or description"
    ),
    include_inactive : bool = Query(False, description="Include inactive features"),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    result = await service.list_features(
        skip=skip,
        limit=limit,
        search=search,
        include_inactive=include_inactive,
    )
    return {"status": "success", "data": result}


@router.get(
    "/{feature_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get feature by ID",
)
async def get_feature(
    feature_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    feature = await service.get_feature(feature_id)
    return {"status": "success", "data": FeatureResponse.model_validate(feature)}


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new feature",
)
async def create_feature(
    feature_data: FeatureCreate,
    current_user: User = Depends(require_permission("create_feature")),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    feature = await service.create_feature(feature_data)
    return {
        "status": "success",
        "message": "Feature created successfully",
        "data": feature,
    }


@router.put(
    "/{feature_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update an existing feature",
)
async def update_feature(
    feature_id: UUID,
    update_data: FeatureUpdate,
    current_user: User = Depends(require_permission("features:write")),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    feature = await service.update_feature(feature_id, update_data)
    return {
        "status": "success",
        "message": "Feature updated successfully",
        "data": FeatureResponse.model_validate(feature),
    }

@router.delete(
    "/{feature_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete a feature",   
)
async def delete_feature(
    feature_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(require_permission("features:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    if hard_delete:
        await service.delete_feature(feature_id)
    else:
        await service.soft_delete_feature(feature_id)
    return {
        "status": "success",
        "message": f"Feature {'hard ' if hard_delete else 'soft '}deleted successfully",
    }