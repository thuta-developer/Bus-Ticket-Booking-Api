import uuid
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.bus_company_repository import BusCompanyRepository
from app.services.cloudinary_upload import (
    upload_to_cloudinary,
    delete_from_cloudinary,
    extract_public_id_from_url,
)


class LogoUploadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BusCompanyRepository(db)

    # ===========================================
    # file validation
    # ===========================================
    def validate_file(self, file: UploadFile) -> None:
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )

    # ============================================
    # Upload Logo (Main Method)
    # ============================================
    async def upload_logo(
        self,
        company_id: str,
        file: UploadFile,
    ) -> Dict[str, Any]:
        """
        Upload logo for a company to Cloudinary.
        """
        # 1. Check if company exists
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        # 2. Validate file
        self.validate_file(file)

        # 3. Generate public_id (for Cloudinary)
        public_id = f"companies/{company_id}_{uuid.uuid4().hex[:8]}"

        # 4. Upload to Cloudinary
        try:
            logo_url = await upload_to_cloudinary(
                file=file,
                folder="companies",
                public_id=public_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload logo: {str(e)}"
            )

        # 5. Delete old logo if exists
        if company.logo_url:
            old_public_id = extract_public_id_from_url(company.logo_url)
            if old_public_id:
                await delete_from_cloudinary(old_public_id)

        # 6. Update database
        company.logo_url = logo_url
        await self.db.commit()
        await self.db.refresh(company)

        return {
            "company_id": company.id,
            "logo_url": logo_url,
            "message": "Logo uploaded successfully"
        }

    # ============================================
    # Delete Logo
    # ============================================
    async def delete_logo(self, company_id: str) -> Dict[str, Any]:
        # 1. Check if company exists
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        # 2. Check if logo exists
        if not company.logo_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Logo not found for this company"
            )

        # 3. Delete from Cloudinary
        public_id = extract_public_id_from_url(company.logo_url)
        if public_id:
            await delete_from_cloudinary(public_id)

        # 4. Update database
        company.logo_url = None
        await self.db.commit()
        await self.db.refresh(company)

        return {
            "company_id": company.id,
            "message": "Logo deleted successfully"
        }




