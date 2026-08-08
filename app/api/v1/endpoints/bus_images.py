from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.services.bus_image_service import BusImageService


router = APIRouter(
    prefix="/bus-images",
    tags=["Bus Images"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Not found"},
    },
)


# ============================================
# 1. Upload Single Image
# ============================================
@router.post(
    "/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload bus image",
    description="Upload a single image for a bus. Max 10 images per bus.",
)
async def upload_bus_image(
    bus_id: UUID,
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WEBP)"),
    is_primary: bool = Query(False, description="Set as primary image"),
    current_user: User = Depends(require_permission("buses:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a single image for a bus.
    """
    service = BusImageService(db)
    image = await service.upload_bus_image(bus_id, file, is_primary)
    return {
        "status": "success",
        "message": "Image uploaded successfully",
        "data": image
    }


# ============================================
# 2. Upload Multiple Images
# ============================================
@router.post(
    "/multiple/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple bus images",
    description="Upload multiple images for a bus. Max 10 images total per bus.",
)
async def upload_multiple_bus_images(
    bus_id: UUID,
    files: List[UploadFile] = File(..., description="Image files (JPEG, PNG, WEBP)"),
    current_user: User = Depends(require_permission("buses:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload multiple images for a bus.
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 images allowed per request"
        )

    service = BusImageService(db)
    images = await service.upload_multiple_images(bus_id, files)
    return {
        "status": "success",
        "message": f"Uploaded {len(images)} images successfully",
        "data": images
    }




# ============================================
# 4. Delete Single Image
# ============================================
@router.delete(
    "/{image_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete bus image",
    description="Delete a specific bus image from Cloudinary and database.",
)
async def delete_bus_image(
    image_id: UUID,
    bus_id: UUID = Query(..., description="Bus ID"),
    current_user: User = Depends(require_permission("buses:delete")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a specific bus image.
    """
    service = BusImageService(db)
    result = await service.delete_image(bus_id, image_id)
    return {
        "status": "success",
        "message": result["message"],
        "data": {
            "image_id": result["image_id"]
        }
    }


# ============================================
# 5. Delete All Images
# ============================================
@router.delete(
    "/all/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete all bus images",
    description="Delete all images for a bus.",
)
async def delete_all_bus_images(
    bus_id: UUID,
    current_user: User = Depends(require_permission("buses:delete")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete all images for a bus.
    """
    service = BusImageService(db)
    result = await service.delete_all_images(bus_id)
    return {
        "status": "success",
        "message": result["message"]
    }


# ============================================
# 6. List Bus Images (Public)
# ============================================
@router.get(
    "/bus/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List bus images",
    description="Get all images for a bus (public endpoint).",
)
async def list_bus_images(
    bus_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all images for a bus.
    """
    service = BusImageService(db)
    images = await service.list_images(bus_id)
    return {
        "status": "success",
        "data": images
    }


# ============================================
# 7. Reorder Images
# ============================================
@router.put(
    "/reorder/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Reorder bus images",
    description="Reorder images for a bus.",
)
async def reorder_bus_images(
    bus_id: UUID,
    image_ids: List[UUID],
    current_user: User = Depends(require_permission("buses:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Reorder images for a bus.
    """
    service = BusImageService(db)
    images = await service.reorder_images(bus_id, image_ids)
    return {
        "status": "success",
        "message": "Images reordered successfully",
        "data": images
    }