# app/services/feature_service.py
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.feature_repository import FeatureRepository
from app.schemas.feature import FeatureCreate, FeatureUpdate, FeatureResponse

class FeatureService:
    def __init__(self, db: AsyncSession):
        self.repo = FeatureRepository(db)

    # Create
    async def create_feature(self, data: FeatureCreate) -> FeatureResponse:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Feature with name '{data.name}' already exists"
            )
        
        feature = await self.repo.create(data.model_dump())
        return FeatureResponse.model_validate(feature)

    # Read
    async def get_feature(self, feature_id: UUID) -> FeatureResponse:
        feature = await self.repo.get_by_id(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature with ID '{feature_id}' not found"
            )
        return FeatureResponse.model_validate(feature)

    async def list_features(
        self, skip: int = 0, limit: int = 20, search: Optional[str] = None, include_inactive: bool = False
    ) -> Dict[str, Any]:
        features = await self.repo.get_all(skip=skip, limit=limit, search=search, include_inactive=include_inactive)
        total = await self.repo.count(search=search, include_inactive=include_inactive)
        
        items = [FeatureResponse.model_validate(f) for f in features]
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "search": search
        }

    # Update
    async def update_feature(self, feature_id: UUID, update_data: FeatureUpdate) -> FeatureResponse:
        existing_feature = await self.repo.get_by_id(feature_id)
        if not existing_feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found"
            )

        if update_data.name:
            name_check = await self.repo.get_by_name(update_data.name)
            if name_check and name_check.id != feature_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Feature name already exists"
                )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields to update"
            )

        updated_feature = await self.repo.update(feature_id, update_dict)
        return FeatureResponse.model_validate(updated_feature)

    # Delete
    async def delete_feature(self, feature_id: UUID) -> None:
        await self.get_feature(feature_id)
        deleted = await self.repo.delete(feature_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found"
            )

    async def soft_delete_feature(self, feature_id: UUID) -> None:
        await self.get_feature(feature_id)
        deleted = await self.repo.soft_delete(feature_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found"
            )