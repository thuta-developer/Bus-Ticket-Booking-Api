from typing import Dict, Optional, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bus_company import BusCompany
from app.repositories.bus_company_repository import BusCompanyRepository
from app.schemas.bus_company import BusCompanyCreate, BusCompanyUpdate,BusCompanyResponse


class BusCompanyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BusCompanyRepository(db)

    
    # Create #
    async def create_company(self, company_data: BusCompanyCreate) -> BusCompany:
        existing = await self.repository.get_by_name(company_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Company '{company_data.name}' already exists"
            )
        
        try:
            return await self.repository.create(company_data.model_dump())
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
    # Read #
    async def get_company(self, company_id: UUID) -> BusCompany:
        company = await self.repository.get_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID '{company_id}' not found"
            )
        return company
    
    async def list_companies(self, skip: int = 0, limit: int = 10, search: Optional[str] = None, include_inactive: bool = False) -> Dict[str, Any]:
        companies = await self.repository.get_all(skip, limit, search, include_inactive)
        total = await self.repository.count(search, include_inactive)

        items = [BusCompanyResponse.model_validate(company) for company in companies]

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "search": search,
        }
    
    # Update #
    async def update_company(self, company_id: UUID, update_data: BusCompanyUpdate) -> BusCompany:
        await self.get_company(company_id)  # Ensure company exists
        
        if update_data.name:
            existing = await self.repository.get_by_name(update_data.name)
            if existing and existing.id != company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Company '{update_data.name}' already exists"
                )
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        try:
            company = await self.repository.update(company_id, update_dict)
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found for update"
                )
            return company
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
    # Delete #
    async def delete_company(self, company_id: UUID) -> None:
        await self.get_company(company_id)  # Ensure company exists
        deleted = await self.repository.delete(company_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID '{company_id}' not found for deletion"
            )

    async def soft_delete_company(self, company_id: UUID) -> None:
        await self.get_company(company_id)  # Ensure company exists
        deleted = await self.repository.soft_delete(company_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID '{company_id}' not found for deletion"
            )
