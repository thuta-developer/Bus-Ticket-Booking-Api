from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.bus_repository import BusRepository
from app.repositories.bus_image_repository import BusImageRepository
from app.schemas.bus_image import BusImageCreate, BusImageResponse
from app.services.cloudinary_upload import (
    upload_to_cloudinary,
    delete_from_cloudinary,
    extract_public_id_from_url,
)


class BusImageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.image_repo = BusImageRepository(db)
        self.bus_repo = BusRepository(db)

    async def upload_bus_image(
        self,
        bus_id: UUID,
        file: UploadFile,
    ) -> BusImageResponse:
        bus = await self.bus_repo.get_by_id(bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bus with id {bus_id} not found.",
            )

        current_count = await self.image_repo.count_by_bus(bus_id)
        if current_count >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 images allowed per bus",
            )

        public_id = f"bus_{bus_id}_{uuid.uuid4().hex[:8]}"
        try:
            image_url = await upload_to_cloudinary(
                file=file,
                folder="bus_images",
                public_id=public_id,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}",
            )
        max_order = await self.image_repo.get_max_order(bus_id)
        image_data = BusImageCreate(
            bus_id=bus_id, image_url=image_url, order=max_order + 1
        )
        image = await self.image_repo.create(image_data.model_dump())
        return BusImageResponse.model_validate(image)

    # ============================================
    # Upload Multiple Images
    # ============================================
    async def upload_multiple_images(
        self,
        bus_id: UUID,
        files: List[UploadFile],
    ) -> List[BusImageResponse]:
        bus = await self.bus_repo.get_by_id(bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found"
            )

        current_count = await self.image_repo.count_by_bus(bus_id)
        if current_count + len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum 10 images allowed. Current: {current_count}, Uploading: {len(files)}"
            )
        results = []

        for i , file in enumerate(files):
            result = await self.upload_bus_image(bus_id, file)
            results.append(result)
        return results

    async def delete_image(self, bus_id: UUID, image_id: UUID) -> Dict[str, Any]:
        bus = await self.bus_repo.get_by_id(bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found"
            )

        image = await self.image_repo.get_by_id(image_id)
        if not image or image.bus_id != bus_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
            )

        public_id = extract_public_id_from_url(image.image_url)
        if public_id:
            await delete_from_cloudinary(public_id)

        await self.image_repo.delete(image_id)
        return {"message": "Image deleted successfully", "image_id": image_id}

    # ============================================
    # Delete All Images
    # ============================================
    async def delete_all_images(self, bus_id: UUID) -> Dict[str, Any]:
        # Check if bus exists
        bus = await self.bus_repo.get_by_id(bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found"
            )
        images = await self.image_repo.get_by_bus(bus_id)
        for image in images:
            public_id = extract_public_id_from_url(image.image_url)
            if public_id:
                await delete_from_cloudinary(public_id)
        count = await self.image_repo.delete_all_by_bus(bus_id)
        return {"message": f"Deleted {count} images for bus {bus_id}"}

    async def list_images(self, bus_id: UUID) -> List[BusImageResponse]:
        images = await self.image_repo.get_by_bus(bus_id)
        return [BusImageResponse.model_validate(img) for img in images]

    # ============================================
    # Reorder Images
    # ============================================
    async def reorder_images(
        self,
        bus_id: UUID,
        image_ids: List[UUID],
    ) -> List[BusImageResponse]:
        """Reorder images by provided order."""
        # Check if bus exists
        bus = await self.bus_repo.get_by_id(bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found"
            )

        # Update order for each image
        for idx, image_id in enumerate(image_ids):
            await self.image_repo.update(image_id, {"order": idx + 1})

        # Return updated list
        return await self.list_images(bus_id)


