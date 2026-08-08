from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.bus_repository import BusRepository
from app.repositories.bus_company_repository import BusCompanyRepository
from app.schemas.bus import BusCreate, BusUpdate, BusResponse


class BusService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BusRepository(db)
        self.company_repo = BusCompanyRepository(db)


    # Create #
    async def create_bus(self, bus_data: BusCreate) -> BusResponse:
        # Check if bus number exists
        existing = await self.repo.get_by_bus_number(bus_data.bus_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bus with number '{bus_data.bus_number}' already exists"
            )
        
        # Check if license plate exists
        existing = await self.repo.get_by_license_plate(bus_data.license_plate)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bus with license plate '{bus_data.license_plate}' already exists"
            )
        
        # Check if company exists
        company = await self.company_repo.get_by_id(bus_data.company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Company with ID '{bus_data.company_id}' does not exist"
            )

        bus_dict = bus_data.model_dump(exclude={"features_ids"})
        feature_ids = bus_data.feature_ids
        
        try:
            bus = await self.repo.create(bus_dict, feature_ids)
            return BusResponse.model_validate(bus)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


    # Read #
    async def get_bus(self, bus_id: UUID) -> BusResponse:
        bus = await self.repo.get_by_id(bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bus with ID '{bus_id}' not found"
            )

        # add company name
        response = BusResponse.model_validate(bus)
        if bus.company:
            response.company_name = bus.company.name
        return response

    async def list_buses(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        company_id: Optional[UUID] = None,
        bus_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        buses = await self.repo.get_all(skip=skip, limit=limit, search=search, company_id=company_id, bus_type=bus_type, include_inactive=include_inactive)
        total = await self.repo.count(search=search, company_id=company_id, bus_type=bus_type, include_inactive=include_inactive)

        item = []
        for bus in buses:
            response = BusResponse.model_validate(bus)
            if bus.company:
                response.company_name = bus.company.name
            item.append(response)

        return {
            "items": item,
            "total": total,
            "skip": skip,
            "limit": limit,
            "search": search
        }

    # Update #
    async def update_bus(self, bus_id: UUID, update_data: BusUpdate) -> BusResponse:
        # check if bus exists
        existing_bus = await self.repo.get_by_id(bus_id)
        if not existing_bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bus Not Found."
            )


        # Check bus number conflict
        if update_data.bus_number:
            existing = await self.repo.get_by_bus_number(update_data.bus_number)
            if existing and existing.id != bus_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bus with number '{update_data.bus_number}' already exists"
                )

        # Check license plate conflict
        if update_data.license_plate:
            existing = await self.repo.get_by_license_plate(update_data.license_plate)
            if existing and existing.id != bus_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bus with license plate '{update_data.license_plate}' already exists"
                )


        # Check company if provided
        if update_data.company_id:
            company = await self.company_repo.get_by_id(update_data.company_id)
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Company with ID '{update_data.company_id}' does not exist"
                )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )


        update_dict = update_data.model_dump(exclude_unset=True, exclude={"feature_ids"})
        feature_ids = update_data.feature_ids if "feature_ids" in update_data.model_dump(exclude_unset=True) else None

        try:
            bus = await self.repo.update(bus_id, update_dict, feature_ids)
            if not bus:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bus not found for update"
                )
            return BusResponse.model_validate(bus)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Delete #
    async def delete_bus(self, bus_id: UUID) -> None:
        await self.get_bus(bus_id)
        deleted = await self.repo.delete(bus_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bus with ID '{bus_id}' not found"
            )

    async def soft_delete_bus(self, bus_id: UUID) -> None:
        # Check if bus exists
        await self.get_bus(bus_id)

        deleted = await self.repo.soft_delete(bus_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found"
            )
